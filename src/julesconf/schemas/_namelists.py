"""Top-level `JulesNamelists` schema combining all 29 namelist files.

Usage:

    from julesconf.schemas import JulesNamelists

    config = JulesNamelists.from_toml("config.toml")
    config.to_namelists("/path/to/jules/namelists")

A JULES run is configured by 29 Fortran namelist files. This module also
provides a TOML front-end to them: `from_toml` / `to_toml` for the readable
single-file form, and `from_namelists` / `to_namelists` for the form JULES
itself consumes.

Writing namelists is deliberately *not* the inverse of reading them: every
field julesconf holds a default for is written explicitly, so the namelists
fully determine the run rather than relying on JULES's internal defaults.
"""

import contextlib
import tomllib
import warnings
from collections.abc import Iterator
from enum import IntEnum
from functools import cache
from os import PathLike
from pathlib import Path
from typing import Any, get_args

import tomli_w
from pydantic import BaseModel, create_model, model_validator
from pydantic.fields import FieldInfo

from julesconf.schemas._base import (
    NamelistModel,
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
    _warn_repeated_groups,
    repeated_group_model,
)
from julesconf.schemas._conditional import (
    fail_if,
    warn_discouraged,
    warn_inactive,
)
from julesconf.schemas.ancillaries import AncillariesNamelist
from julesconf.schemas.constraints import (
    SIBLING_DIMS,
    ListLen,
    PerElementDefault,
)
from julesconf.schemas.crop_params import CropParamsNamelist
from julesconf.schemas.drive import DriveNamelist
from julesconf.schemas.fire import FireNamelist
from julesconf.schemas.imogen import ImogenNamelist
from julesconf.schemas.initial_conditions import InitialConditionsNamelist
from julesconf.schemas.jules_deposition import JulesDepositionNamelist
from julesconf.schemas.jules_hydrology import JulesHydrologyNamelist
from julesconf.schemas.jules_irrig import JulesIrrigNamelist
from julesconf.schemas.jules_prnt_control import JulesPrntControlNamelist
from julesconf.schemas.jules_radiation import JulesRadiationNamelist
from julesconf.schemas.jules_rivers import JulesRiversNamelist
from julesconf.schemas.jules_snow import JulesSnowNamelist
from julesconf.schemas.jules_soil import JulesSoilNamelist
from julesconf.schemas.jules_soil_biogeochem import JulesSoilBiogeochemNamelist
from julesconf.schemas.jules_surface import JulesSurfaceNamelist
from julesconf.schemas.jules_surface_types import JulesSurfaceTypesNamelist
from julesconf.schemas.jules_vegetation import JulesVegetationNamelist
from julesconf.schemas.jules_water_resources import JulesWaterResourcesNamelist
from julesconf.schemas.model_environment import ModelEnvironmentNamelist
from julesconf.schemas.model_grid import ModelGridNamelist
from julesconf.schemas.nveg_params import NvegParamsNamelist
from julesconf.schemas.output import OutputNamelist
from julesconf.schemas.pft_params import PftParamsNamelist
from julesconf.schemas.prescribed_data import PrescribedDataNamelist
from julesconf.schemas.science_fixes import ScienceFixesNamelist
from julesconf.schemas.timesteps import TimestepsNamelist
from julesconf.schemas.triffid_params import TriffidParamsNamelist
from julesconf.schemas.urban import UrbanNamelist

__all__ = [
    "POSTPONED_NAMELISTS",
    "REPEATABLE_GROUPS",
    "JulesNamelists",
    "PostponedNamelistWarning",
]

_STANDALONE_TEMP_FIXES = (
    "l_dtcanfix",
    "l_fix_alb_ice_thick",
    "l_fix_albsnow_ts",
    "l_fix_neg_snow",
    "l_fix_ustar_dust",
    "l_fix_wind_snow",
)
"""`JULES_TEMP_FIXES` members upstream expects to be true in standalone JULES.

The six boolean members carrying a rose rule of the form "this should be
`.true.` in JULES standalone". `ctile_orog_fix` carries the seventh but is an
enum rather than a switch, so it is checked separately.
"""

POSTPONED_NAMELISTS = frozenset(
    {
        "cable_pfts",
        "cable_prognostics",
        "cable_soil",
        "cable_soilparm",
        "cable_surface_types",
        "oasis_rivers",
        "red_params",
    }
)
"""Namelists JULES supports but julesconf deliberately does not.

These configure rarely-used extensions (the CABLE land surface scheme, OASIS
river coupling, the RED demography model) that are out of scope. A config
using them is not an error, but julesconf silently ignoring them would look
like support, so `PostponedNamelistWarning` is emitted instead. See
`AGENTS.md`.
"""


class PostponedNamelistWarning(UserWarning):
    """A config referenced a namelist julesconf deliberately does not support.

    Distinct from `UnknownNamelistKeyWarning`, which concerns unknown *members*
    within a namelist julesconf does model. This concerns a known-but-unsupported
    *file*, so the two can be escalated independently:

        warnings.simplefilter("error", PostponedNamelistWarning)
    """


def find_list_len(field_info: FieldInfo) -> ListLen | None:
    """Return the `ListLen` metadata for a field, if it has any.

    Pydantic only surfaces metadata from the outermost `Annotated` in
    `FieldInfo.metadata`, so `Annotated[list[X], ListLen(...)] | None`
    hides the marker inside a union member. This searches the full annotation
    so both that spelling and the canonical
    `Annotated[list[X] | None, ListLen(...)]` resolve.

    Args:
        field_info: The Pydantic field to inspect.

    Returns:
        The first `ListLen` found, or `None` if the field has none.
    """
    for meta in field_info.metadata:
        if isinstance(meta, ListLen):
            return meta
    return _find_in_annotation(field_info.annotation)


def _find_in_annotation(annotation: Any) -> ListLen | None:
    """Recursively search an annotation's type arguments for a `ListLen`."""
    for arg in get_args(annotation):
        if isinstance(arg, ListLen):
            return arg
        found = _find_in_annotation(arg)
        if found is not None:
            return found
    return None


def find_per_element_default(field_info: FieldInfo) -> PerElementDefault | None:
    """Return the `PerElementDefault` metadata for a field, if it has any.

    Args:
        field_info: The Pydantic field to inspect.

    Returns:
        The first `PerElementDefault` found, or `None` if the field has none.
    """
    for meta in field_info.metadata:
        if isinstance(meta, PerElementDefault):
            return meta
    return None


def _to_enum_names(value: Any) -> Any:
    """Recursively replace `IntEnum` members with their names, for TOML output."""
    if isinstance(value, IntEnum):
        return value.name
    if isinstance(value, dict):
        return {k: _to_enum_names(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_enum_names(v) for v in value]
    return value


def _resolve_dims(surface_types: Any) -> dict[str, int]:
    """Resolve the cross-namelist dimension names against `jules_surface_types`.

    Args:
        surface_types: The validated `JULES_SURFACE_TYPES` block.

    Returns:
        A mapping of every name in `LIST_LEN_DIMS` to its size.
    """
    npft, nnvg, ncpft = surface_types.npft, surface_types.nnvg, surface_types.ncpft
    return {
        "npft": npft,
        "nnpft": npft - ncpft,
        "nnvg": nnvg,
        "ncpft": ncpft,
        "ntype": npft + nnvg,
    }


def _resolve_sibling_dims(
    model: NamelistModel, meta: ListLen, dims: dict[str, int]
) -> dict[str, int] | None:
    """Return `dims` extended with any sibling dimension `meta` names.

    Args:
        model: The block carrying the field, and hence the sibling member.
        meta: The field's `ListLen` metadata.
        dims: Globally-resolved dimension sizes (`npft`, `nnvg`, …).

    Returns:
        A mapping resolving every name `meta` uses, or `None` if a sibling is
        unset or zero, meaning the block is inactive and the check is skipped.
    """
    siblings = {d for d in (meta.dim, *meta.tolerates) if d in SIBLING_DIMS}
    if not siblings:
        return dims

    local = dict(dims)
    for dim in siblings:
        length = getattr(model, dim, 0) or 0
        if length <= 0:
            return None
        local[dim] = length
    return local


def _repeatable_groups() -> frozenset[str]:
    """Collect the namelist groups julesconf models as lists of blocks."""
    names = set()
    for namelist in JulesNamelists.model_fields.values():
        model = namelist.annotation
        if not (isinstance(model, type) and issubclass(model, NamelistModel)):
            continue
        for block, info in model.model_fields.items():
            if repeated_group_model(info.annotation) is not None:
                names.add(block)
    return frozenset(names)


def _warn_postponed_files(directory: str | PathLike) -> None:
    """Emit a `PostponedNamelistWarning` for each postponed `.nml` in a directory."""
    for name in sorted(POSTPONED_NAMELISTS):
        if (Path(directory) / f"{name}.nml").is_file():
            warnings.warn(
                f"{name}.nml is a JULES namelist that julesconf does not"
                " support; it will be ignored and omitted from any namelists"
                " written",
                PostponedNamelistWarning,
                stacklevel=3,
            )


def _expand_per_element_defaults(
    model: NamelistModel, data: dict[str, Any], dims: dict[str, int]
) -> None:
    """Fill in `PerElementDefault` fields, in place, on a dumped config.

    Walks the model tree alongside the dumped dict. A marked field that the
    user left unset is written as its scalar default repeated to the full
    length of its dimension, because Fortran namelist input does not broadcast
    a scalar across an array.

    Args:
        model: The model whose fields to inspect.
        data: The corresponding dumped dict, modified in place.
        dims: Globally-resolved dimension sizes (`npft`, `nnvg`, …).
    """
    for field_name, field_info in type(model).model_fields.items():
        value = getattr(model, field_name)

        if isinstance(value, NamelistModel):
            sub = data.get(field_name)
            if isinstance(sub, dict):
                _expand_per_element_defaults(value, sub, dims)
            continue

        if repeated_group_model(field_info.annotation) is not None:
            # A repeated group (`jules_output_profile`, …) is a list of blocks,
            # each with its own sibling dimensions. Expand each one against
            # its own `nvars` rather than the first one's.
            blocks = data.get(field_name)
            if isinstance(blocks, list):
                for block, dumped in zip(value, blocks, strict=True):
                    if isinstance(dumped, dict):
                        _expand_per_element_defaults(block, dumped, dims)
            continue

        meta = find_per_element_default(field_info)
        if meta is None or value is not None:
            # Either not a per-element field, or the user supplied a value:
            # in both cases leave the dumped output alone.
            continue

        if meta.dim in SIBLING_DIMS:
            length = getattr(model, meta.dim, 0) or 0
        else:
            length = dims[meta.dim]

        # A zero-length dimension means the block is inactive. Writing an empty
        # assignment would be invalid namelist syntax, so omit the member.
        if length > 0:
            data[field_name] = [meta.value] * length


@contextlib.contextmanager
def _strict_warnings(strict: bool) -> Iterator[None]:
    """Escalate the warnings `strict` covers, for the duration of the block.

    Args:
        strict: If `True`, turn everything julesconf cannot represent into an
            error. If `False`, the block runs under the ambient filters.

    Yields:
        Nothing; the context is entered for its warning filter alone.
    """
    with warnings.catch_warnings():
        if strict:
            warnings.simplefilter("error", UnknownNamelistKeyWarning)
            warnings.simplefilter("error", RepeatedNamelistGroupWarning)
        yield


@cache
def _single_namelist_model(name: str) -> type[BaseModel]:
    """Build a one-field wrapper model around a single namelist's schema.

    Validating `jules_soil.nml` on its own could call
    `JulesSoilNamelist.model_validate` directly, but then pydantic would locate
    a failure at `('jules_soil', 'dzsoil_io')` — block, member — where the same
    failure found by a whole-directory read is located at
    `('jules_soil', 'jules_soil', 'dzsoil_io')` — file, block, member. Wrapping
    the model in a single-field model named after the file restores the leading
    element, so `julesconf._errors` renders the two identically with no special
    case of its own.

    Args:
        name: A field of `JulesNamelists`, which is also the `.nml` stem.

    Returns:
        A model with exactly that one required field. Cached, so repeated
        validation of the same namelist does not rebuild it.
    """
    info = JulesNamelists.model_fields[name]
    return create_model(
        f"Single_{name}",
        __module__=__name__,
        **{name: (info.annotation, ...)},  # type: ignore[call-overload]
    )


class JulesNamelists(NamelistModel):
    """Schema for a complete JULES namelists directory.

    Validates a dict of the form returned by
    `julesconf.config.NamelistConfig.read`, applying both
    per-namelist constraints and cross-namelist consistency checks.
    """

    ancillaries: AncillariesNamelist = AncillariesNamelist()
    crop_params: CropParamsNamelist = CropParamsNamelist()
    drive: DriveNamelist
    fire: FireNamelist = FireNamelist()
    imogen: ImogenNamelist = ImogenNamelist()
    initial_conditions: InitialConditionsNamelist
    jules_deposition: JulesDepositionNamelist = JulesDepositionNamelist()
    jules_hydrology: JulesHydrologyNamelist
    jules_irrig: JulesIrrigNamelist = JulesIrrigNamelist()
    jules_prnt_control: JulesPrntControlNamelist = JulesPrntControlNamelist()
    jules_radiation: JulesRadiationNamelist
    jules_rivers: JulesRiversNamelist = JulesRiversNamelist()
    jules_snow: JulesSnowNamelist = JulesSnowNamelist()
    jules_soil: JulesSoilNamelist
    jules_soil_biogeochem: JulesSoilBiogeochemNamelist = JulesSoilBiogeochemNamelist()
    jules_surface: JulesSurfaceNamelist
    jules_surface_types: JulesSurfaceTypesNamelist
    jules_vegetation: JulesVegetationNamelist
    jules_water_resources: JulesWaterResourcesNamelist = JulesWaterResourcesNamelist()
    model_environment: ModelEnvironmentNamelist
    model_grid: ModelGridNamelist = ModelGridNamelist()
    nveg_params: NvegParamsNamelist
    output: OutputNamelist = OutputNamelist()
    pft_params: PftParamsNamelist
    prescribed_data: PrescribedDataNamelist = PrescribedDataNamelist()
    science_fixes: ScienceFixesNamelist = ScienceFixesNamelist()
    timesteps: TimestepsNamelist
    triffid_params: TriffidParamsNamelist = TriffidParamsNamelist()
    urban: UrbanNamelist = UrbanNamelist()

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown_keys(cls, data: Any) -> Any:
        """Warn about unknown top-level keys, distinguishing postponed namelists.

        Overrides `NamelistModel._warn_unknown_keys` so that a postponed
        namelist produces `PostponedNamelistWarning` rather than the generic
        unknown-key warning.
        """
        if isinstance(data, dict):
            repeated = _warn_repeated_groups(cls, data)
            for key in sorted(set(data) - set(cls.model_fields) - repeated):
                if key in POSTPONED_NAMELISTS:
                    warnings.warn(
                        f"{key!r} is a JULES namelist that julesconf does not"
                        " support; it will be ignored and omitted from any"
                        " namelists written",
                        PostponedNamelistWarning,
                        stacklevel=2,
                    )
                else:
                    warnings.warn(
                        f"{cls.__name__}: ignoring unknown namelist member {key!r}",
                        UnknownNamelistKeyWarning,
                        stacklevel=2,
                    )
        return data

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @classmethod
    def _validate(
        cls, data: dict, *, strict: bool, allow_grouped: bool = False
    ) -> "JulesNamelists":
        """Validate a config dict, optionally rejecting unknown members.

        Assembly of the grouped form happens *inside* the warning filter, so
        `strict` catches a mistyped parameter on a `[[pft]]` entry too.
        """
        from julesconf.schemas._grouped import assemble, is_grouped

        with _strict_warnings(strict):
            if allow_grouped and is_grouped(data):
                data = assemble(data)
            return cls.model_validate(data)

    @classmethod
    def from_namelists(
        cls, directory: str | PathLike, *, strict: bool = False
    ) -> "JulesNamelists":
        """Read and validate a JULES namelists directory.

        Args:
            directory: Path to a directory containing the 29 `.nml` files.
            strict: If `True`, raise on anything julesconf cannot represent —
                an unmodelled namelist member, or a namelist group that occurs
                more than once. Both are dropped, so a read-then-write cycle
                would lose them; use `strict` when the result is destined for
                `to_namelists`.

        Returns:
            The validated configuration.

        Raises:
            UnknownNamelistKeyWarning: If `strict` and an unknown member is found.
            RepeatedNamelistGroupWarning: If `strict` and a namelist group
                occurs more than once.
        """
        from julesconf.config import NamelistConfig

        _warn_postponed_files(directory)
        return cls._validate(NamelistConfig().read(directory), strict=strict)

    @classmethod
    def namelist_field(cls, path: str | PathLike) -> str:
        """Resolve a `.nml` path to the field of this model it belongs to.

        The fields of `JulesNamelists` are named one-to-one after the namelist
        files, so the mapping is the file stem. This is the same correspondence
        `from_namelists` relies on, exposed so that a caller holding one file
        can find its schema without hard-coding a second copy of the table.

        Args:
            path: Path to a `.nml` file. Only its stem is looked at; the file
                does not have to exist.

        Returns:
            The field name, which is also the name of the namelist.

        Raises:
            ValueError: If the stem is not a namelist julesconf models, either
                because it is one of `POSTPONED_NAMELISTS` or because it is not
                a JULES namelist at all.
        """
        name = Path(path).stem
        if name in POSTPONED_NAMELISTS:
            raise ValueError(
                f"{name}.nml is a JULES namelist that julesconf deliberately"
                " does not model, so there is nothing to validate it against"
            )
        if name not in cls.model_fields:
            raise ValueError(
                f"{name}.nml is not a JULES namelist file julesconf models;"
                f" expected one of: {', '.join(sorted(cls.model_fields))}"
            )
        return name

    @classmethod
    def from_namelist_file(
        cls, path: str | PathLike, *, strict: bool = False
    ) -> NamelistModel:
        """Read and validate a **single** namelist file against its own schema.

        The file is matched to its schema by name, exactly as `from_namelists`
        does — `jules_soil.nml` against the `jules_soil` field of this model.

        Only that namelist's own rules are applied. The cross-namelist rules
        live on `JulesNamelists` and cannot run here: the list-length checks
        need the dimensions declared in `jules_surface_types.nml`, and the
        consistency rules read switches from other files. A file that passes
        this check may still be rejected by `from_namelists`, so this is a
        faster, weaker check and not a substitute for validating the directory.

        Args:
            path: Path to one `.nml` file.
            strict: If `True`, raise on anything julesconf cannot represent, as
                `from_namelists` does.

        Returns:
            The validated namelist model — the same object `from_namelists`
            would leave on the corresponding field of `JulesNamelists`.

        Raises:
            ValueError: If the file is not a namelist julesconf models.
        """
        from julesconf.config import NamelistFileHandler

        name = cls.namelist_field(path)
        data = NamelistFileHandler().read(path)
        with _strict_warnings(strict):
            wrapper = _single_namelist_model(name).model_validate({name: data})
        return getattr(wrapper, name)

    @classmethod
    def from_toml(
        cls, path: str | PathLike, *, strict: bool = False
    ) -> "JulesNamelists":
        """Read and validate a TOML configuration file.

        Args:
            path: Path to a `.toml` file. Either form is accepted and
                detected automatically: the flat form, laid out as
                `[<namelist>.<block>]` tables mirroring the namelist
                structure; or the grouped form, using `[[pft]]`,
                `[[crop_pft]]` and `[[nvg]]` arrays of tables for the
                surface-type parameters.
            strict: If `True`, raise on any member julesconf does not model,
                or any namelist group that occurs more than once.

        Returns:
            The validated configuration.

        Raises:
            UnknownNamelistKeyWarning: If `strict` and an unknown member is found.
            RepeatedNamelistGroupWarning: If `strict` and a namelist group
                occurs more than once.
            GroupedConfigError: If a grouped config mixes the two forms or
                specifies a parameter on only some entries of a group.
        """
        with open(path, "rb") as f:
            return cls._validate(tomllib.load(f), strict=strict, allow_grouped=True)

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def to_namelist_dict(self) -> dict[str, Any]:
        """Return the config as a dict ready for `NamelistConfig.write`.

        Every field julesconf holds a default for is included, and
        `PerElementDefault` fields are expanded to their full length, so the
        result fully determines the run. Fields julesconf has no value for are
        omitted.

        Returns:
            A `{namelist: {block: {member: value}}}` dict of plain JSON types.
        """
        data = self.model_dump(mode="json", exclude_none=True)
        surface_types = self.jules_surface_types.jules_surface_types
        _expand_per_element_defaults(self, data, _resolve_dims(surface_types))
        return data

    def to_namelists(
        self, directory: str | PathLike, *, overwrite_ok: bool = False
    ) -> None:
        """Write the config to a JULES namelists directory.

        Args:
            directory: Destination directory; created if it does not exist.
            overwrite_ok: If `True`, overwrite existing `.nml` files.
        """
        from julesconf.config import NamelistConfig

        NamelistConfig().write(
            directory, self.to_namelist_dict(), overwrite_ok=overwrite_ok
        )

    def to_toml_dict(self, *, grouped: bool = True) -> dict[str, Any]:
        """Return the config as a dict ready for TOML serialisation.

        Unlike `to_namelist_dict`, `PerElementDefault` fields are *not*
        expanded — a TOML config stays terse — and enum fields are written as
        member names rather than integers.

        Args:
            grouped: If `True`, pivot the surface-type parameters into `pft`,
                `crop_pft` and `nvg` arrays of tables. If `False`, emit the
                flat form that mirrors the namelists one-to-one.

        Returns:
            A config dict, in the requested form.
        """
        from julesconf.schemas._grouped import disassemble

        data = _to_enum_names(self.model_dump(exclude_none=True))
        return disassemble(data) if grouped else data

    def to_toml(self, path: str | PathLike, *, grouped: bool = True) -> None:
        """Write the config to a TOML file.

        Args:
            path: Destination `.toml` file.
            grouped: If `True` (the default), write the grouped form, in which
                each surface type is one `[[pft]]` / `[[crop_pft]]` / `[[nvg]]`
                table rather than a position in 113 parallel arrays. Pass
                `False` for the flat form, which mirrors the namelists exactly
                and is the more faithful choice when migrating a config whose
                arrays are longer than JULES reads.

        The file is replaced only once it has been rendered in full: the TOML
        is written to a temporary file beside the destination and moved into
        place. Nothing can therefore leave a half-written config behind, which
        matters most when the destination is also the source, as it is for an
        in-place reformat.
        """
        destination = Path(path)
        data = self.to_toml_dict(grouped=grouped)
        staged = destination.with_name(f".{destination.name}.julesconf-tmp")
        try:
            with open(staged, "wb") as f:
                tomli_w.dump(data, f)
            staged.replace(destination)
        finally:
            staged.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Cross-namelist conditional rules
    #
    # Each of these transcribes one or more `fail-if` / `trigger` rules from
    # the JULES rose metadata whose condition names a member of a *different*
    # block, which the block itself cannot see. Which upstream rule each check
    # implements is recorded in `tests/data/rose_meta/rules_disposition.toml`.
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _check_triffid_consistency(self) -> "JulesNamelists":
        """Check the soil carbon model against TRIFFID."""
        from julesconf.schemas.jules_soil_biogeochem import SoilBgcModel

        model = self.jules_soil_biogeochem.jules_soil_biogeochem.soil_bgc_model
        triffid = self.jules_vegetation.jules_vegetation.l_triffid
        fail_if(
            model == SoilBgcModel.single_pool and triffid,
            "Can't use 1-pool with TRIFFID",
        )
        fail_if(
            model == SoilBgcModel.four_pool and not triffid,
            "Can't use 4-pool soil C without TRIFFID",
        )
        fail_if(
            model == SoilBgcModel.ecosse and not triffid,
            "Can't use ECOSSE without TRIFFID",
        )
        return self

    @model_validator(mode="after")
    def _check_irrigation_consistency(self) -> "JulesNamelists":
        """Check the irrigation switches against the schemes they depend on."""
        from julesconf.schemas.jules_rivers import RiverRoutingAlgorithm

        irrig = self.jules_irrig.jules_irrig
        rivers = self.jules_rivers.jules_rivers
        fail_if(
            irrig.l_irrig_dmd and self.jules_soil.jules_soil.l_holdwater,
            "Irrigation can't be used with l_holdwater = TRUE",
        )
        if irrig.l_irrig_limit:
            fail_if(not rivers.l_rivers, "l_rivers must TRUE if l_irrig_limit = TRUE")
            fail_if(
                rivers.i_river_vn != RiverRoutingAlgorithm.standalone_trip,
                "i_river_vn must be 3 (trip) if l_irrig_limit = TRUE",
            )
            fail_if(
                not self.jules_hydrology.jules_hydrology.l_top,
                "l_top must TRUE if l_irrig_limit = TRUE",
            )
            fail_if(
                self.jules_water_resources.jules_water_resources.l_water_irrigation,
                "l_irrig_limit must be F if l_water_irrigation=T",
            )
        return self

    @model_validator(mode="after")
    def _check_um_only_options(self) -> "JulesNamelists":
        """Check options that are available only to, or only outside, the UM."""
        from julesconf.schemas.jules_rivers import RiverRoutingAlgorithm
        from julesconf.schemas.jules_vegetation import StomataModel
        from julesconf.schemas.model_environment import JulesParent

        parent = self.model_environment.jules_model_environment.l_jules_parent
        veg = self.jules_vegetation.jules_vegetation
        rivers = self.jules_rivers.jules_rivers
        if parent == JulesParent.um:
            fail_if(self.jules_soil.jules_soil.l_tile_soil, "Not available in the UM")
            fail_if(veg.l_red, "RED is not available to the UM.")
            fail_if(veg.l_sugar, "SUGAR is not available to the UM.")
            fail_if(
                veg.fsmc_shape == 1,
                "Piece-wise linear in soil potential is not currently available to the UM. Should be 0 (volumetric soil moisture).",
            )
            fail_if(
                veg.stomata_model == StomataModel.sox,
                "stomata_model = sox is not available to the UM",
            )
            fail_if(
                self.jules_water_resources.jules_water_resources.l_water_resources,
                "Must be false in the UM.",
            )
            fail_if(
                self.jules_surface_types.jules_surface_types.ncpft > 0,
                "This is not available to the UM. Should be zero.",
            )
            fail_if(
                self.jules_irrig.jules_irrig.l_irrig_limit,
                "Irrigation limitation is not tested in the UM yet.",
            )
            fail_if(
                rivers.i_river_vn
                not in (None, RiverRoutingAlgorithm.um_trip, RiverRoutingAlgorithm.rfm),
                "UM_TRIP and RFM are the only options compatible with the UM.",
            )
        else:
            fail_if(
                rivers.i_river_vn == RiverRoutingAlgorithm.um_trip,
                "UM_TRIP is not compatible with standalone.",
            )
            fail_if(
                self.jules_surface.jules_surface.iscrntdiag in (2, 3),
                "The preferred option in standalone is 0. The decoupled option"
                " specified is not recommended until driving JULES with a"
                " decoupled variable is fully tested.",
            )
        fail_if(
            rivers.l_riv_overbank and parent != JulesParent.standalone,
            "Overbank inundation is not available to the UM or OASIS.",
        )
        if parent == JulesParent.standalone:
            self._check_standalone_only_options()
        return self

    def _check_standalone_only_options(self) -> None:
        """Reject the options JULES implements only for its UM coupling.

        Each of these is a rose `fail-if` naming `l_jules_parent == 0`
        explicitly, so none of them applies to a CABLE parent. They are grouped
        here rather than left in their own blocks because none of those blocks
        can see `JULES_MODEL_ENVIRONMENT`.

        Raises:
            ValueError: If a UM-only option is selected in standalone.
        """
        from julesconf.schemas.jules_surface import FormDrag, IModiscOpt, SrfExCnvGust

        surface = self.jules_surface.jules_surface
        fail_if(
            surface.formdrag != FormDrag.no_orographic_stress,
            "In standalone formdrag should be 0",
        )
        fail_if(
            surface.i_modiscopt != IModiscOpt.off,
            "In standalone i_modiscopt should be 0",
        )
        fail_if(
            surface.srf_ex_cnv_gust != SrfExCnvGust.off,
            "This is not currently available to standalone.",
        )
        fail_if(
            surface.l_vary_z0m_soil,
            "Variable roughness length of bare soil is currently not available to standalone.",
        )
        fail_if(
            self.jules_radiation.jules_radiation.l_sea_alb_var_chl,
            "This is not currently available to standalone.",
        )
        fail_if(
            self.jules_vegetation.jules_vegetation.l_trif_init_accum,
            "This is only applicable to the UM so should be false in standalone",
        )

    @model_validator(mode="after")
    def _warn_temp_fixes_off_in_standalone(self) -> "JulesNamelists":
        """Warn for each JULES_TEMP_FIXES correction switched off in standalone.

        The rose metadata carries seven rules of the form "this should be
        `.true.` in JULES standalone" — a bug fix the model's authors expect a
        standalone run to have on. julesconf defaults all seven to the
        corrected behaviour, so this fires only when a configuration turns one
        back off deliberately.

        Advisory rather than fatal, unlike the other rules in this class.
        Upstream writes them as `fail-if`, but reproducing a historical run is
        a legitimate reason to disable a fix, and refusing to model that would
        make julesconf unable to describe configurations JULES itself will
        happily execute. The warning makes the choice visible instead.
        """
        from julesconf.schemas.model_environment import JulesParent
        from julesconf.schemas.science_fixes import CtileOrogFix

        if self.model_environment.jules_model_environment.l_jules_parent != (
            JulesParent.standalone
        ):
            return self
        fixes = self.science_fixes.jules_temp_fixes
        for member in _STANDALONE_TEMP_FIXES:
            warn_discouraged(
                not getattr(fixes, member),
                f"{member} should be .true. in JULES standalone.",
            )
        warn_discouraged(
            fixes.ctile_orog_fix != CtileOrogFix.correct_sea_only,
            "ctile_orog_fix should be 2 in JULES standalone.",
        )
        return self

    @model_validator(mode="after")
    def _check_vegetation_consistency(self) -> "JulesNamelists":
        """Check vegetation options against the blocks they read from."""
        veg = self.jules_vegetation.jules_vegetation
        fail_if(
            veg.l_red and self.jules_surface_types.jules_surface_types.ncpft > 0,
            "RED cannot be used with crop PFTs (ncpft > 0)",
        )
        fail_if(
            veg.fsmc_shape == 1
            and not (veg.l_use_pft_psi and self.ancillaries.jules_soil_props.const_z),
            "1. Piece-wise linear in soil potential. Currently only allowed when"
            " const_z = T and l_use_pft_psi = T.",
        )
        return self

    @model_validator(mode="after")
    def _check_urban_consistency(self) -> "JulesNamelists":
        """Check the urban schemes against the surface types and ancillaries."""
        urban = self.urban.jules_urban
        types = self.jules_surface_types.jules_surface_types
        two_tile = (types.urban_canyon or 0) > 0 or (types.urban_roof or 0) > 0
        fail_if(
            urban.l_moruses_albedo and not self.jules_radiation.jules_radiation.l_cosz,
            "Requires l_cosz = TRUE",
        )
        fail_if(
            self.jules_surface.jules_surface.l_urban2t and not two_tile,
            "When l_urban2t there must be a canyon and a roof surface type",
        )
        fail_if(
            two_tile and self.ancillaries.urban_properties.nvars == 0,
            "Urban properties need to be supplied when using two-tile urban schemes",
        )
        return self

    @model_validator(mode="after")
    def _check_deposition_consistency(self) -> "JulesNamelists":
        """Check the deposition options against the tiling and the parent model.

        JULES's deposition routines are called from UKCA, so which of them are
        reachable depends on whether JULES is coupled to the UM. Every check
        below the first is gated on `l_deposition`: the block is inert when
        deposition is off, exactly as `JulesDeposition._warn_inactive_members`
        reports, and applying these rules to an inert block would make a UM
        configuration that does no deposition at all invalid for the sake of a
        switch JULES never reads. See `notes/UPSTREAM.md` §4.4.
        """
        from julesconf.schemas.jules_deposition import DepH2SoilScheme
        from julesconf.schemas.model_environment import JulesParent

        deposition = self.jules_deposition.jules_deposition
        fail_if(
            deposition.l_deposition and self.jules_surface.jules_surface.l_aggregate,
            "Deposition does not work with aggregated tile",
        )
        if not deposition.l_deposition:
            return self
        parent = self.model_environment.jules_model_environment.l_jules_parent
        if parent == JulesParent.um:
            fail_if(
                deposition.dep_h2_soil_scheme == DepH2SoilScheme.paulot,
                "The Paulot et al. H2 scheme is not yet fully implemented for UM-coupled JULES applications (when JULES deposition called from UKCA): only Conrad & Seiler scheme available, dep_h2_soil_scheme = 1",
            )
            fail_if(
                not deposition.l_deposition_from_ukca,
                "For UM_JULES applications, only the call to the deposition routines from the UKCA is currently available",
            )
            fail_if(
                deposition.l_deposition_gc_corr,
                "For UM_JULES applications, stomatal conductance corrected for bare soil evaporation is not available in the UKCA",
            )
        elif parent == JulesParent.standalone:
            fail_if(
                deposition.l_deposition_from_ukca,
                "Deposition switch cannot be true in JULES standalone as JULES-based deposition routines called from UKCA",
            )
            fail_if(
                deposition.l_ukca_ddepo3_ocean,
                "Deposition switch not available in JULES standalone as requires >75% open water fraction",
            )
            fail_if(
                deposition.l_ukca_dry_dep_so2wet,
                "Deposition switch not fully implemented in JULES standalone",
            )
        return self

    @model_validator(mode="after")
    def _check_surface_height_lengths(self) -> "JulesNamelists":
        """Check the surface-elevation arrays against the number of tiles.

        `l_elev_absolute_height`, `surf_hgt_io` and `surf_hgt_band` are all
        `nsurft`-length, which is `npft + nnvg` unless the tiles are
        aggregated. julesconf carries no `nsurft` dimension, so these cannot go
        through the `ListLen` machinery and are checked here, where
        `JULES_SURFACE` and `JULES_SURFACE_TYPES` are both in view.

        Each check is gated on the member actually being read. Upstream's
        `fail-if` rules do not repeat the conditions of their own `trigger`
        rules, because rose never evaluates a `fail-if` on a setting a trigger
        has deactivated — see `notes/UPSTREAM.md` §4.1. Applied ungated they
        would reject the common shape where `zero_height` is TRUE and a stray
        elevation array is left over from an earlier edit.

        Raises:
            ValueError: If an array that JULES reads has the wrong length.
        """
        surf_hgt = self.model_grid.jules_surf_hgt
        z_land = self.model_grid.jules_z_land
        types = self.jules_surface_types.jules_surface_types
        nsurft = (
            1
            if self.jules_surface.jules_surface.l_aggregate
            else types.npft + types.nnvg
        )

        def check(block: str, member: str, value: list | None) -> None:
            fail_if(
                value is not None and len(value) != nsurft,
                f"{block}: {member} has {len(value or ())} element(s), expected"
                f" nsurft={nsurft}",
            )

        if not surf_hgt.zero_height:
            check(
                "jules_surf_hgt",
                "l_elev_absolute_height",
                surf_hgt.l_elev_absolute_height,
            )
        if not surf_hgt.use_file:
            check("jules_surf_hgt", "surf_hgt_io", surf_hgt.surf_hgt_io)
        if surf_hgt.elevations_are_absolute:
            check("jules_z_land", "surf_hgt_band", z_land.surf_hgt_band)
        return self

    @model_validator(mode="after")
    def _check_imogen_consistency(self) -> "JulesNamelists":
        """IMOGEN runs use a 360-day calendar and start at the turn of a year."""
        if self.imogen.imogen_onoff_switch.l_imogen:
            fail_if(
                not self.timesteps.jules_time.l_360,
                "This should be .true. in IMOGEN.",
            )
            fail_if(
                "01-01 00:00:00" not in self.timesteps.jules_time.main_run_start,
                "IMOGEN runs must start at 00:00:00 on 1st Jan for some year",
            )
        return self

    @model_validator(mode="after")
    def _warn_inactive_across_namelists(self) -> "JulesNamelists":
        """Warn about members a switch in *another* namelist makes inactive."""
        from julesconf.schemas.jules_vegetation import CanModel

        if not self.jules_hydrology.jules_hydrology.l_top:
            warn_inactive(
                self.jules_soil_biogeochem.jules_soil_biogeochem,
                ("ch4_substrate", "l_ch4_tlayered", "l_ch4_interactive"),
                because="jules_hydrology l_top is false, so there is no"
                " wetland fraction to emit methane from",
            )
        if not self.jules_vegetation.jules_vegetation.l_triffid:
            warn_inactive(
                self.ancillaries.jules_agric,
                ("zero_agric", "zero_past"),
                because="jules_vegetation l_triffid is false",
            )
        if self.jules_vegetation.jules_vegetation.can_model != CanModel.radiative_snow:
            warn_inactive(
                self.jules_snow.jules_snow,
                (
                    "cansnowpft",
                    "snowinterceptfact",
                    "snowloadlai",
                    "snowunloadfact",
                ),
                because="jules_vegetation can_model is not radiative_snow",
            )

        from julesconf.schemas.jules_vegetation import PhotoAcclimModel, PhotoActModel

        veg = self.jules_vegetation.jules_vegetation
        if veg.photo_acclim_model != PhotoAcclimModel.no_acclimation:
            warn_inactive(
                self.pft_params.jules_pftparm,
                ("ds_jmax_io", "ds_vcmax_io"),
                because="jules_vegetation photo_acclim_model is not"
                " no_acclimation, so the entropy factors come from dsj_coef"
                " and dsv_coef instead",
            )
        if veg.photo_acclim_model not in (
            PhotoAcclimModel.thermal_adaptation,
            PhotoAcclimModel.adaptation_and_acclimation,
        ):
            # The block exists solely to prescribe `t_home_gb`, which only
            # thermal *adaptation* uses.
            warn_inactive(
                self.ancillaries.jules_vegetation_props,
                tuple(type(self.ancillaries.jules_vegetation_props).model_fields),
                because="jules_vegetation photo_acclim_model is neither"
                " thermal_adaptation nor adaptation_and_acclimation, so no"
                " spatially varying vegetation property is read",
            )
        if veg.photo_act_model != PhotoActModel.vary_by_pft:
            warn_inactive(
                self.pft_params.jules_pftparm,
                ("act_jmax_io", "act_vcmax_io"),
                because="jules_vegetation photo_act_model is not vary_by_pft,"
                " so the activation energies come from act_j_coef and"
                " act_v_coef instead",
            )
        if not veg.l_ag_expand:
            warn_inactive(
                self.triffid_params.jules_triffid,
                ("ag_expand_io",),
                because="jules_vegetation l_ag_expand is false",
            )
        return self

    @model_validator(mode="after")
    def _check_list_lengths(self) -> "JulesNamelists":
        """Check every `ListLen`-marked list against its dimension.

        Walks the whole model tree rather than a fixed set of namelists, so a
        `ListLen` field added anywhere is checked automatically.
        """
        surface_types = self.jules_surface_types.jules_surface_types
        self._check_model_list_lengths(self, "", _resolve_dims(surface_types))
        return self

    @staticmethod
    def _check_model_list_lengths(
        model: NamelistModel, path: str, dims: dict[str, int]
    ) -> None:
        """Recursively validate `ListLen` fields on `model` and its submodels.

        Cross-namelist dimensions come from `dims`; a sibling dimension
        (`nvars`) is read off `model` itself, so each block is checked against
        its own value. A sibling that is unset or zero marks the block inactive
        and skips the check — see `ListLen`.

        A repeated group is descended into per element, so each output profile
        is checked against *its own* `nvars` rather than the first profile's.
        The index appears in the path 1-based, as JULES and rose number the
        groups: `output.jules_output_profile(2).var`.
        """
        for field_name, field_info in type(model).model_fields.items():
            value = getattr(model, field_name)
            field_path = f"{path}.{field_name}" if path else field_name

            if isinstance(value, NamelistModel):
                JulesNamelists._check_model_list_lengths(value, field_path, dims)
                continue

            if repeated_group_model(field_info.annotation) is not None:
                for index, block in enumerate(value or [], start=1):
                    JulesNamelists._check_model_list_lengths(
                        block, f"{field_path}({index})", dims
                    )
                continue

            meta = find_list_len(field_info)
            if meta is None or not isinstance(value, list):
                continue

            local = _resolve_sibling_dims(model, meta, dims)
            if local is None:
                continue

            accepted = meta.accepted_lengths(local)
            if len(value) not in accepted:
                expected = " or ".join(
                    f"{d}={local[d]}" for d in (meta.dim, *meta.tolerates)
                )
                raise ValueError(
                    f"{field_path} has {len(value)} element(s), expected {expected}"
                )


REPEATABLE_GROUPS: frozenset[str] = _repeatable_groups()
"""Namelist groups julesconf models as a list of blocks, one per occurrence.

Derived from the schemas — every field annotated `list[<block model>]` — so
declaring a new repeatable group is a one-line change to that block's
namelist model and nothing else.

`julesconf.config.NamelistFileHandler` reads these into a `list[dict]` however
many times they occur, including once, and writes one Fortran group per entry.
Normalising here rather than in the schemas keeps the one-vs-many ambiguity
where it comes from: `f90nml` returns a bare block for a single occurrence and
a `Cogroup` for several, and nothing downstream should have to know that.
"""
