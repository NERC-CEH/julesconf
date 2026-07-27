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
See `notes/toml_config.md`.
"""

import tomllib
import warnings
from enum import IntEnum
from os import PathLike
from pathlib import Path
from typing import Any, get_args

import tomli_w
from pydantic import model_validator
from pydantic.fields import FieldInfo

from julesconf.schemas._base import (
    NamelistModel,
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
    _warn_repeated_groups,
    repeated_group_model,
)
from julesconf.schemas._conditional import fail_if, warn_inactive
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

        with warnings.catch_warnings():
            if strict:
                warnings.simplefilter("error", UnknownNamelistKeyWarning)
                warnings.simplefilter("error", RepeatedNamelistGroupWarning)
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
        """
        with open(path, "wb") as f:
            tomli_w.dump(self.to_toml_dict(grouped=grouped), f)

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
        """Dry deposition needs the individual surface tiles."""
        fail_if(
            self.jules_deposition.jules_deposition.l_deposition
            and self.jules_surface.jules_surface.l_aggregate,
            "Deposition does not work with aggregated tile",
        )
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
