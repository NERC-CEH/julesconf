"""Grouped configuration form: `[[pft]]`, `[[crop_pft]]` and `[[nvg]]`.

JULES parameterises surface types with parallel arrays scattered across five
namelist files. Configuring one plant functional type means editing 78 separate
list members, each of which must have the right length and put its value at the
right index — and nothing in the config says that element 3 of `canht_ft_io` and
element 3 of `g_area_io` describe the same thing.

This module pivots those arrays into arrays-of-tables, so each surface type is
one object:

    [[pft]]
    name = "broadleaf"
    type = "brd_leaf"
    canht_ft = 19.01
    lai = 5.0

`npft`, `ncpft` and `nnvg` disappear from the config surface — they are the
lengths of the three arrays — as do the `jules_surface_types` index members,
which are reconstructed from each entry's `type` key and its position.

The entry models are **generated** from the `ListLen` metadata already on the
flat schemas rather than hand-written. A hand-written 78-field `Pft` would be a
second copy of the schema that drifts at the first JULES version bump; deriving
it means bounds, validators and field documentation carry over automatically,
and a new `ListLen` field appears in the grouped form with no further work.
`test_grouped_models.py` guards that property from the other side.

`assemble` and `disassemble` are dict-to-dict and are exact inverses (modulo the
two cases documented below), which keeps `JulesNamelists` itself unaware of the
grouped form.
"""

import dataclasses
import warnings
from typing import Any, Union, get_args, get_origin

from pydantic import create_model, model_validator
from pydantic.fields import FieldInfo

from julesconf.schemas._base import (
    REPEATED_GROUP_MARK,
    NamelistModel,
    UnknownNamelistKeyWarning,
    iter_leaf_fields,
)
from julesconf.schemas._namelists import JulesNamelists, find_list_len
from julesconf.schemas.constraints import LIST_LEN_DIMS
from julesconf.schemas.jules_surface_types import JulesSurfaceTypes

__all__ = [
    "GROUPED_KEYS",
    "CropPft",
    "GroupedConfigError",
    "Nvg",
    "Pft",
    "ToleratedLengthWarning",
    "assemble",
    "disassemble",
    "is_grouped",
]

GROUPED_KEYS = ("pft", "crop_pft", "nvg")
"""The top-level keys of the grouped form, in surface-type order."""

CONTRIBUTORS: dict[str, tuple[str, ...]] = {
    "npft": ("pft", "crop_pft"),
    "nnpft": ("pft",),
    "ncpft": ("crop_pft",),
    "nnvg": ("nvg",),
    "ntype": ("pft", "crop_pft", "nvg"),
}
"""Which groups contribute elements to each dimension, in array order.

This is the single source of truth for both membership and ordering. JULES
requires vegetated surfaces first, with crop PFTs occupying the trailing PFT
positions (`jules_surface_types.nml.rst:39,41`, `crop_params.nml.rst:13`), and
reads only the leading `nnpft` values of each TRIFFID array
(`triffid_params.nml.rst:17`).
"""

GROUP_DIMS: dict[str, tuple[str, ...]] = {
    group: tuple(dim for dim, groups in CONTRIBUTORS.items() if group in groups)
    for group in GROUPED_KEYS
}
"""Which dimensions each group carries fields for. Derived from `CONTRIBUTORS`."""

VEG_TYPE_IDS = frozenset(
    {
        "brd_leaf",
        "brd_leaf_dec",
        "brd_leaf_eg_trop",
        "brd_leaf_eg_temp",
        "ndl_leaf",
        "ndl_leaf_dec",
        "ndl_leaf_eg",
        "c3_grass",
        "c3_crop",
        "c3_pasture",
        "c4_grass",
        "c4_crop",
        "c4_pasture",
        "shrub",
        "shrub_dec",
        "shrub_eg",
    }
)
"""Surface type identifiers valid at a vegetated position (`1:npft`).

Crop *identifiers* (`c3_crop`, `c4_crop`) are deliberately permitted on
`[[pft]]` as well as `[[crop_pft]]`: the surface type ID and the crop model
(`ncpft`) are independent in JULES, and restricting them would reject legal
configurations.
"""

NVG_TYPE_IDS = frozenset(
    {
        "urban",
        "lake",
        "soil",
        "ice",
        "urban_canyon",
        "urban_roof",
        "elev_ice",
        "elev_rock",
    }
)
"""Surface type identifiers valid at a non-vegetated position (`npft+1:ntype`)."""

SHARED_TYPE_IDS = frozenset({"usr_type"})
"""Surface type identifiers valid at any position (`1:ntype`)."""

DIM_MEMBERS = ("npft", "nnvg", "ncpft")
"""`jules_surface_types` members the grouped form derives rather than reads."""

TYPE_IDS_FOR = {
    "pft": VEG_TYPE_IDS | SHARED_TYPE_IDS,
    "crop_pft": VEG_TYPE_IDS | SHARED_TYPE_IDS,
    "nvg": NVG_TYPE_IDS | SHARED_TYPE_IDS,
}


class GroupedConfigError(ValueError):
    """A grouped configuration is malformed.

    Subclasses `ValueError` so it is also caught by Pydantic-style handling.
    """


class ToleratedLengthWarning(UserWarning):
    """A tolerated over-long array lost its unread trailing elements.

    See `disassemble`. Escalate with:

        warnings.simplefilter("error", ToleratedLengthWarning)
    """


# ---------------------------------------------------------------------------
# The field specification table, built once at import
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FieldSpec:
    """One flat schema field that becomes a key on a grouped entry."""

    toml_name: str
    namelist: str
    block: str
    member: str
    dim: str

    @property
    def path(self) -> str:
        """The dotted path to the flat member, for error messages."""
        return f"{self.namelist}.{self.block}.{self.member}"


def _strip_io(member: str) -> str:
    """Return a namelist member name without its `_io` suffix.

    JULES suffixes many parameter arrays with `_io` to distinguish the namelist
    input from the internal variable. The suffix carries no meaning for a user
    writing a config, and stripping it is verified collision-free at import.
    """
    return member[:-3] if member.endswith("_io") else member


def _element_type(annotation: Any) -> Any:
    """Return the element type of a list annotation, looking through unions.

    Handles `list[X]`, `list[X] | None` and `Annotated[list[X] | None, ...]`.

    Args:
        annotation: The field annotation to unwrap.

    Returns:
        The element type, or `None` if the annotation admits no list.
    """
    if get_origin(annotation) is list:
        return get_args(annotation)[0]
    for arg in get_args(annotation):
        if arg is type(None):
            continue
        found = _element_type(arg)
        if found is not None:
            return found
    return None


def _optional(annotation: Any) -> Any:
    """Return `annotation | None`, spelled so `Annotated` element types survive."""
    return Union[annotation, None]  # noqa: UP007


def _build_specs() -> tuple[FieldSpec, ...]:
    """Collect every `ListLen` field in the flat schemas into a spec table."""
    specs = []
    for path, name, info in iter_leaf_fields(JulesNamelists):
        meta = find_list_len(info)
        if meta is None or meta.dim not in LIST_LEN_DIMS:
            # `ListLen` also marks namelist-local lengths (`nvars`), which are
            # not surface-type dimensions and have no place in a grouped entry.
            continue
        if any(part.endswith(REPEATED_GROUP_MARK) for part in path):
            # A field inside a repeated group cannot be pivoted onto a surface
            # type: with N groups there are N independent arrays of it, and a
            # single [[pft]] entry has room for one value. JULES_DEPOSITION_
            # SPECIES::rsurf_std_io is the only case — one ntype-length surface
            # resistance array *per species*. It stays in the flat form, where
            # each species keeps its own, and is still length-checked per
            # species by JulesNamelists._check_model_list_lengths.
            continue
        if len(path) != 2:
            # A ListLen field reached through anything else would break the
            # flat-dict indexing in assemble/disassemble.
            raise GroupedConfigError(
                f"{'.'.join((*path, name))} carries ListLen but is not a "
                "namelist.block.member field; the grouped form cannot index it"
            )
        element = _element_type(info.annotation)
        if element is None:
            raise GroupedConfigError(
                f"{'.'.join((*path, name))} carries ListLen but is not a list"
            )
        specs.append(
            FieldSpec(
                toml_name=_strip_io(name),
                namelist=path[0],
                block=path[1],
                member=name,
                dim=meta.dim,
            )
        )
    return tuple(specs)


SPECS = _build_specs()
SPECS_BY_DIM: dict[str, tuple[FieldSpec, ...]] = {
    dim: tuple(s for s in SPECS if s.dim == dim) for dim in CONTRIBUTORS
}

if set(SPECS_BY_DIM) != LIST_LEN_DIMS:
    raise GroupedConfigError(
        f"CONTRIBUTORS covers {sorted(SPECS_BY_DIM)} but LIST_LEN_DIMS is "
        f"{sorted(LIST_LEN_DIMS)}; every dimension needs a group"
    )


# ---------------------------------------------------------------------------
# The generated entry models
# ---------------------------------------------------------------------------


class GroupedEntry(NamelistModel):
    """Base for a single `[[pft]]` / `[[crop_pft]]` / `[[nvg]]` entry.

    Inherits `extra="ignore"` plus unknown-key warnings from `NamelistModel`,
    so a parameter written on the wrong group (`t_bse` on a `[[pft]]`) warns
    rather than being silently accepted, and `strict=True` turns it into an
    error.
    """

    name: str | None = None
    """A label for this surface type. Documentary only; never written to the
    namelists, and so not preserved by a round-trip through the flat form."""

    type: str | None = None
    """The `jules_surface_types` identifier for this surface type, e.g.
    `brd_leaf`. Optional: JULES does not require every surface type to have
    one."""

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown_keys(cls, data: Any) -> Any:
        """Phrase the unknown-key warning for the grouped surface."""
        if isinstance(data, dict):
            for key in sorted(set(data) - set(cls.model_fields)):
                warnings.warn(
                    f"{cls.__name__}: ignoring unknown parameter {key!r}",
                    UnknownNamelistKeyWarning,
                    stacklevel=2,
                )
        return data


def _make_entry_model(group: str) -> type[GroupedEntry]:
    """Generate the entry model for one group from the flat schemas."""
    flat = {name: info for _, name, info in iter_leaf_fields(JulesNamelists)}
    fields: dict[str, Any] = {}
    for dim in GROUP_DIMS[group]:
        for spec in SPECS_BY_DIM[dim]:
            info = flat[spec.member]
            element = _element_type(info.annotation)
            fields[spec.toml_name] = (
                _optional(element),
                FieldInfo(default=None, description=info.description),
            )
    model = create_model(
        {"pft": "Pft", "crop_pft": "CropPft", "nvg": "Nvg"}[group],
        __base__=GroupedEntry,
        __module__=__name__,
        **fields,
    )
    return model


Pft = _make_entry_model("pft")
"""One natural plant functional type. Generated; see the module docstring."""

CropPft = _make_entry_model("crop_pft")
"""One crop plant functional type. Generated; see the module docstring."""

Nvg = _make_entry_model("nvg")
"""One non-vegetated surface type. Generated; see the module docstring."""

ENTRY_MODELS: dict[str, type[GroupedEntry]] = {
    "pft": Pft,
    "crop_pft": CropPft,
    "nvg": Nvg,
}


# ---------------------------------------------------------------------------
# Assembly: grouped -> flat
# ---------------------------------------------------------------------------


def is_grouped(data: dict) -> bool:
    """Return whether a config dict uses the grouped form.

    Args:
        data: A parsed TOML config.

    Returns:
        `True` if any of `pft`, `crop_pft` or `nvg` is present at top level.
    """
    return any(key in data for key in GROUPED_KEYS)


def _label(group: str, index: int, entry: dict) -> str:
    """Return a human-locatable label for an entry, for error messages."""
    tag = entry.get("name") or entry.get("type")
    return f"{group}[{index}]" + (f" ({tag!r})" if tag else "")


def _validated_entries(data: dict) -> dict[str, list[dict]]:
    """Pop and validate the grouped tables, returning plain dicts."""
    entries: dict[str, list[dict]] = {}
    for group in GROUPED_KEYS:
        raw = data.pop(group, [])
        if not isinstance(raw, list) or not all(isinstance(e, dict) for e in raw):
            raise GroupedConfigError(
                f"{group!r} must be an array of tables, e.g. [[{group}]]"
            )
        model = ENTRY_MODELS[group]
        validated = []
        for index, item in enumerate(raw):
            entry = model.model_validate(item)
            if entry.type is not None and entry.type not in TYPE_IDS_FOR[group]:
                valid = "a non-vegetated" if group == "nvg" else "a vegetated"
                raise GroupedConfigError(
                    f"{_label(group, index, item)}: {entry.type!r} is not "
                    f"{valid} surface type identifier"
                )
            validated.append(entry.model_dump(exclude_none=True))
        entries[group] = validated
    return entries


def _reject_flat_duplicates(data: dict, ntype: int) -> None:
    """Reject flat members that the grouped form is responsible for."""
    clashes = [
        spec.path
        for spec in SPECS
        if isinstance(data.get(spec.namelist), dict)
        and isinstance(data[spec.namelist].get(spec.block), dict)
        and spec.member in data[spec.namelist][spec.block]
    ]

    surface = (data.get("jules_surface_types") or {}).get("jules_surface_types") or {}
    clashes += [
        f"jules_surface_types.jules_surface_types.{member}"
        for member in DIM_MEMBERS
        if member in surface
    ]
    # An index member is only a clash if it names a real position. A sentinel
    # such as -1 means "this surface type is not in use", which the grouped
    # form cannot express and disassemble deliberately leaves in place.
    clashes += [
        f"jules_surface_types.jules_surface_types.{member}"
        for member, value in surface.items()
        if member not in DIM_MEMBERS and isinstance(value, int) and 1 <= value <= ntype
    ]

    if clashes:
        raise GroupedConfigError(
            "config mixes the grouped and flat forms; these are derived from "
            f"[[pft]] / [[crop_pft]] / [[nvg]] and must not also be set "
            f"directly: {sorted(clashes)}"
        )


def _check_all_or_none(entries: dict[str, list[dict]]) -> None:
    """Reject a parameter set on some entries of a dimension but not others.

    A Fortran namelist array cannot be partially specified — there is no way to
    omit element 3 — so each parameter must be given by every contributing entry
    or by none of them.
    """
    problems = []
    for dim, groups in CONTRIBUTORS.items():
        contributors = [
            (group, index, entry)
            for group in groups
            for index, entry in enumerate(entries[group])
        ]
        if not contributors:
            continue
        for spec in SPECS_BY_DIM[dim]:
            setters = [c for c in contributors if spec.toml_name in c[2]]
            if not setters or len(setters) == len(contributors):
                continue
            missing = next(c for c in contributors if spec.toml_name not in c[2])
            problems.append(
                f"{_label(*missing)} omits {spec.toml_name!r} but "
                f"{_label(*setters[0])} sets it"
            )

    if problems:
        shown = problems[:10]
        extra = f"\n  ... and {len(problems) - 10} more" if len(problems) > 10 else ""
        raise GroupedConfigError(
            "a namelist array cannot be partially specified:\n  "
            + "\n  ".join(shown)
            + extra
        )


def assemble(data: dict) -> dict:
    """Convert a grouped config to the flat namelist-shaped form.

    Args:
        data: A parsed TOML config containing `pft` / `crop_pft` / `nvg`
            arrays of tables. Modified in place and returned.

    Returns:
        The equivalent flat config, ready for `JulesNamelists.model_validate`.

    Raises:
        GroupedConfigError: If the grouped and flat forms are mixed, a
            parameter is specified on only some entries, two entries claim the
            same surface type identifier, or the groups are empty.
    """
    entries = _validated_entries(data)

    nnpft, ncpft, nnvg = (len(entries[g]) for g in GROUPED_KEYS)
    npft = nnpft + ncpft
    if nnpft < 1:
        raise GroupedConfigError(
            "at least one [[pft]] entry is required (JULES requires npft >= 1, "
            "and ncpft < npft, so not every PFT may be a crop)"
        )
    if nnvg < 1:
        raise GroupedConfigError("at least one [[nvg]] entry is required")

    _reject_flat_duplicates(data, npft + nnvg)
    _check_all_or_none(entries)

    for dim, groups in CONTRIBUTORS.items():
        contributors = [e for group in groups for e in entries[group]]
        for spec in SPECS_BY_DIM[dim]:
            block = data.setdefault(spec.namelist, {}).setdefault(spec.block, {})
            if contributors and spec.toml_name in contributors[0]:
                block[spec.member] = [e[spec.toml_name] for e in contributors]

    surface = data.setdefault("jules_surface_types", {}).setdefault(
        "jules_surface_types", {}
    )
    surface.update({"npft": npft, "nnvg": nnvg, "ncpft": ncpft})

    positions: dict[str, int] = {}
    ordered = [
        (group, index, entry)
        for group in GROUPED_KEYS
        for index, entry in enumerate(entries[group])
    ]
    for position, (group, index, entry) in enumerate(ordered, start=1):
        type_id = entry.get("type")
        if type_id is None:
            continue
        if type_id in positions:
            raise GroupedConfigError(
                f"{_label(group, index, entry)}: surface type {type_id!r} is "
                f"already used at position {positions[type_id]}. Each "
                "jules_surface_types member holds a single index, so a type "
                "identifier cannot be reused"
            )
        positions[type_id] = position
        surface[type_id] = position

    return data


# ---------------------------------------------------------------------------
# Disassembly: flat -> grouped
# ---------------------------------------------------------------------------


def _dim_offset(dim: str, position: int, dims: dict[str, int]) -> int:
    """Return the 0-based index into a `dim`-length array for a surface position.

    Args:
        dim: The dimension name.
        position: The 1-based surface type position.
        dims: Resolved dimension sizes.

    Returns:
        The index into the array.
    """
    base = {
        "npft": 0,
        "nnpft": 0,
        "ntype": 0,
        "ncpft": dims["nnpft"],
        "nnvg": dims["npft"],
    }[dim]
    return position - 1 - base


def _group_for(position: int, dims: dict[str, int]) -> str:
    """Return which group a 1-based surface type position belongs to."""
    if position <= dims["nnpft"]:
        return "pft"
    if position <= dims["npft"]:
        return "crop_pft"
    return "nvg"


def disassemble(data: dict) -> dict:
    """Convert a flat config to the grouped form.

    The inverse of `assemble`, with two documented exceptions: entry `name`s
    are not recoverable (they are never written to the namelists), and a
    TRIFFID array supplied at the tolerated `npft` length loses its trailing
    unread elements.

    Args:
        data: A flat config dict. Modified in place and returned.

    Returns:
        The equivalent grouped config, with the arrays of tables first.

    Raises:
        GroupedConfigError: If two surface type identifiers claim the same
            position.
    """
    surface = (data.get("jules_surface_types") or {}).get("jules_surface_types") or {}
    npft, nnvg = surface.get("npft"), surface.get("nnvg")
    ncpft = surface.get("ncpft", 0)
    if not isinstance(npft, int) or not isinstance(nnvg, int):
        raise GroupedConfigError(
            "cannot build the grouped form without jules_surface_types.npft and .nnvg"
        )
    dims = {
        "npft": npft,
        "nnpft": npft - ncpft,
        "ncpft": ncpft,
        "nnvg": nnvg,
        "ntype": npft + nnvg,
    }

    type_at: dict[int, str] = {}
    for member in sorted(set(surface) - set(DIM_MEMBERS)):
        value = surface[member]
        if not isinstance(value, int) or not 1 <= value <= dims["ntype"]:
            # A sentinel ("not in use"); leave it in the flat block so it
            # survives the round-trip.
            continue
        if value in type_at:
            raise GroupedConfigError(
                f"surface type position {value} is claimed by both "
                f"{type_at[value]!r} and {member!r}"
            )
        type_at[value] = member
        del surface[member]

    for member in DIM_MEMBERS:
        surface.pop(member, None)

    groups: dict[str, list[dict]] = {group: [] for group in GROUPED_KEYS}
    for position in range(1, dims["ntype"] + 1):
        group = _group_for(position, dims)
        entry: dict[str, Any] = {}
        if position in type_at:
            entry["type"] = type_at[position]
        groups[group].append(entry)

    for dim, contributing in CONTRIBUTORS.items():
        for spec in SPECS_BY_DIM[dim]:
            block = (data.get(spec.namelist) or {}).get(spec.block) or {}
            values = block.get(spec.member)
            if values is None:
                continue
            if len(values) > dims[dim]:
                warnings.warn(
                    f"{spec.path} has {len(values)} elements but JULES reads "
                    f"only the leading {dim}={dims[dim]}; the trailing "
                    f"{len(values) - dims[dim]} will be dropped from the "
                    "grouped form. Use to_toml(..., grouped=False) to preserve "
                    "them verbatim.",
                    ToleratedLengthWarning,
                    stacklevel=3,
                )
            for position in range(1, dims["ntype"] + 1):
                group = _group_for(position, dims)
                if group not in contributing:
                    continue
                index = _dim_offset(dim, position, dims)
                if 0 <= index < len(values):
                    groups[group][_local_index(group, position, dims)][
                        spec.toml_name
                    ] = values[index]
            del block[spec.member]

    _prune_empty(data)
    grouped = {group: entries for group, entries in groups.items() if entries}
    return {**grouped, **data}


def _local_index(group: str, position: int, dims: dict[str, int]) -> int:
    """Return the index of a surface position within its own group's list."""
    base = {"pft": 0, "crop_pft": dims["nnpft"], "nvg": dims["npft"]}[group]
    return position - 1 - base


def _prune_empty(data: dict) -> None:
    """Drop blocks and namelists left empty by disassembly, in place."""
    for namelist in list(data):
        blocks = data[namelist]
        if not isinstance(blocks, dict):
            continue
        for block in list(blocks):
            if blocks[block] == {}:
                del blocks[block]
        if blocks == {}:
            del data[namelist]


# Guard the assumption that every surface type identifier is classified, so a
# new member added to JulesSurfaceTypes cannot silently become unusable.
_CLASSIFIED = VEG_TYPE_IDS | NVG_TYPE_IDS | SHARED_TYPE_IDS | frozenset(DIM_MEMBERS)
if frozenset(JulesSurfaceTypes.model_fields) != _CLASSIFIED:
    raise GroupedConfigError(
        "unclassified jules_surface_types members: "
        f"{sorted(frozenset(JulesSurfaceTypes.model_fields) - _CLASSIFIED)}"
    )
