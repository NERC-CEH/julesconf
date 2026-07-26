"""Shared base model for JULES namelist schemas."""

import re
import warnings
from collections.abc import Iterator
from functools import cache
from typing import Any, get_args, get_origin

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.fields import FieldInfo

__all__ = [
    "NamelistModel",
    "RepeatedNamelistGroupWarning",
    "UnknownNamelistKeyWarning",
    "iter_leaf_fields",
    "repeated_group_model",
]

REPEATED_GROUP_RE = re.compile(r"^_grp_(?P<name>.+)_(?P<index>\d+)$")
"""Matches the key `f90nml` invents for a namelist group that occurs twice.

Fortran permits the same group to appear several times in one file — JULES
uses this for `jules_output_profile`, `jules_prescribed_dataset` and
`jules_deposition_species`. `f90nml` cannot store them under one dict key, so
it renames every occurrence to `_grp_<group>_<n>`, zero-indexed.

`julesconf.config.NamelistFileHandler` never produces these keys: it reads a
repeated group as a `list[dict]`, one entry per occurrence. A key matching
this pattern therefore means a group julesconf models as a *single* block
turned up more than once, which is real data loss — see
`RepeatedNamelistGroupWarning`.
"""

REPEATED_GROUP_MARK = "[]"
"""Suffix `iter_leaf_fields` appends to the path element of a repeated group.

The walk is over model *classes*, so there is no element index to record;
the marker says only that everything below it lives inside a group that may
occur many times, and so is not addressable as `namelist.block.member`.
"""


def _is_list_annotation(annotation: Any) -> bool:
    """Return whether an annotation admits a list, looking through unions.

    Handles `list[X]`, `list[X] | None` and `Annotated[list[X] | None, ...]`.
    """
    if get_origin(annotation) is list:
        return True
    return any(_is_list_annotation(arg) for arg in get_args(annotation))


def repeated_group_model(annotation: Any) -> type["NamelistModel"] | None:
    """Return the block model of a repeated-group field, if it is one.

    A field annotated `list[SomeNamelistModel]` models a namelist group that
    Fortran permits to occur many times in one file, with one list entry per
    occurrence. Everything that walks the model tree has to descend into these
    per element rather than treating the field as a leaf.

    Args:
        annotation: The field annotation to inspect. `list[X]`, `list[X] | None`
            and `Annotated[list[X] | None, ...]` are all recognised.

    Returns:
        The element model, or `None` if the annotation is not a list of
        `NamelistModel`.
    """
    if get_origin(annotation) is list:
        args = get_args(annotation)
        element = args[0] if args else None
        if isinstance(element, type) and issubclass(element, NamelistModel):
            return element
        return None
    for arg in get_args(annotation):
        found = repeated_group_model(arg)
        if found is not None:
            return found
    return None


class UnknownNamelistKeyWarning(UserWarning):
    """A namelist dict contained keys that the schema does not know and ignored."""


class RepeatedNamelistGroupWarning(UserWarning):
    """A namelist group julesconf models as a single block occurred repeatedly.

    Fortran allows a namelist group to be repeated within one file. The three
    groups JULES itself repeats — `jules_output_profile`,
    `jules_prescribed_dataset` and `jules_deposition_species` — are modelled as
    **lists of blocks** and do not raise this warning: they are read into one
    list entry per occurrence and written back out the same way.

    This warning is what is left over: *any other* group that turns up more
    than once. julesconf models one block of it, so the repetitions cannot be
    represented and are dropped — a read-then-write cycle silently loses every
    occurrence but the first. In practice that means a group JULES gained the
    ability to repeat after v7.9, or a hand-built dict still carrying the
    `_grp_<group>_<n>` keys `f90nml` invents, which
    `julesconf.config.NamelistFileHandler` no longer produces.

    Distinct from `UnknownNamelistKeyWarning`, which concerns a member
    julesconf has never heard of, and from `PostponedNamelistWarning`, which
    concerns a whole namelist file julesconf deliberately excludes. This
    concerns a group julesconf *does* model but can only hold one of, so it is
    a modelling gap rather than a version gap, and is escalated separately:

        import warnings

        from julesconf.schemas import RepeatedNamelistGroupWarning

        warnings.simplefilter("error", RepeatedNamelistGroupWarning)

    See `AGENTS.md`, "Repeated namelist groups".
    """


def _warn_repeated_groups(cls: type, data: dict) -> set[str]:
    """Warn once per repeated namelist group found in `data`.

    Args:
        cls: The model being validated, named in the warning message.
        data: The candidate input dict.

    Returns:
        The keys that matched the repeated-group pattern, so the caller can
        exclude them from the generic unknown-key warning.
    """
    matched: set[str] = set()
    counts: dict[str, int] = {}
    for key in data:
        match = REPEATED_GROUP_RE.match(key)
        if match is not None:
            matched.add(key)
            name = match["name"]
            counts[name] = counts.get(name, 0) + 1

    for name in sorted(counts):
        warnings.warn(
            f"{cls.__name__}: the namelist group {name!r} occurs"
            f" {counts[name]} times; julesconf models a single {name!r} block,"
            " so all but the first are dropped and would be lost by a"
            " read-then-write cycle",
            RepeatedNamelistGroupWarning,
            stacklevel=3,
        )
    return matched


class NamelistModel(BaseModel):
    """Base model for JULES namelist schemas that warns on unknown keys.

    Unknown keys are ignored (`extra="ignore"`) so that configs containing
    members not covered by the schema (e.g. from a different JULES version,
    or gaps in the documentation the schemas were derived from) still
    validate. However, unknown keys are frequently misspellings of real
    members, which JULES itself silently drops, so a
    `UnknownNamelistKeyWarning` is emitted for each one.

    To treat unknown keys as validation errors, escalate the warning:

        import warnings

        from julesconf.schemas import UnknownNamelistKeyWarning

        warnings.simplefilter("error", UnknownNamelistKeyWarning)
    """

    model_config = ConfigDict(extra="ignore", use_attribute_docstrings=True)

    @classmethod
    @cache
    def _list_field_names(cls) -> frozenset[str]:
        """Names of fields that accept a list of *values*, cached per class.

        A repeated group is a list of blocks, not of values, and is excluded:
        the reason for the coercion below does not apply to it, and a config
        must say `[[jules_output_profile]]` even for a single profile.
        """
        return frozenset(
            name
            for name, info in cls.model_fields.items()
            if _is_list_annotation(info.annotation)
            and repeated_group_model(info.annotation) is None
        )

    @model_validator(mode="before")
    @classmethod
    def _coerce_scalars_to_lists(cls, data: Any) -> Any:
        """Wrap a scalar in a list where the schema expects a list.

        Fortran writes a one-element array indistinguishably from a scalar
        (`canht_ft_io = 19.01`), and `f90nml` reads it back as a scalar. Without
        this, a legal single-PFT JULES config fails validation, and any config
        whose lists happen to have one element cannot be round-tripped.
        """
        if not isinstance(data, dict):
            return data

        scalars = {
            name
            for name in cls._list_field_names() & set(data)
            if data[name] is not None and not isinstance(data[name], (list, tuple))
        }
        if not scalars:
            return data
        return {k: [v] if k in scalars else v for k, v in data.items()}

    @model_validator(mode="before")
    @classmethod
    def _warn_unknown_keys(cls, data: Any) -> Any:
        """Emit a warning for each key not known to the schema."""
        if isinstance(data, dict):
            repeated = _warn_repeated_groups(cls, data)
            for key in sorted(set(data) - set(cls.model_fields) - repeated):
                warnings.warn(
                    f"{cls.__name__}: ignoring unknown namelist member {key!r}",
                    UnknownNamelistKeyWarning,
                    stacklevel=2,
                )
        return data


def iter_leaf_fields(
    model: type[NamelistModel], path: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], str, FieldInfo]]:
    """Walk a model tree, yielding every field that is not itself a submodel.

    Several pieces of machinery are driven by field metadata and need the same
    traversal: the `ListLen` length check, `PerElementDefault` expansion, and
    the generated grouped-config models.

    A field holding a *repeated* group (`list[SomeNamelistModel]`) is descended
    into as well, since its members are ordinary namelist members. Its path
    element carries `REPEATED_GROUP_MARK`, so a caller that can only address
    `namelist.block.member` can tell the difference and skip it.

    Args:
        model: The model class to walk.
        path: Field names of the enclosing blocks, used internally.

    Yields:
        `(block_path, field_name, field_info)` for each leaf field.
    """
    for name, info in model.model_fields.items():
        annotation = info.annotation
        if isinstance(annotation, type) and issubclass(annotation, NamelistModel):
            yield from iter_leaf_fields(annotation, (*path, name))
            continue
        repeated = repeated_group_model(annotation)
        if repeated is not None:
            yield from iter_leaf_fields(repeated, (*path, name + REPEATED_GROUP_MARK))
        else:
            yield path, name, info
