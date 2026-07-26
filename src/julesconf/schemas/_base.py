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
]

REPEATED_GROUP_RE = re.compile(r"^_grp_(?P<name>.+)_(?P<index>\d+)$")
"""Matches the key `f90nml` invents for a namelist group that occurs twice.

Fortran permits the same group to appear several times in one file — JULES
uses this for `jules_output_profile`, `jules_prescribed_dataset` and
`jules_deposition_species`. `f90nml` cannot store them under one dict key, so
it renames every occurrence to `_grp_<group>_<n>`, zero-indexed.
"""


def _is_list_annotation(annotation: Any) -> bool:
    """Return whether an annotation admits a list, looking through unions.

    Handles `list[X]`, `list[X] | None` and `Annotated[list[X] | None, ...]`.
    """
    if get_origin(annotation) is list:
        return True
    return any(_is_list_annotation(arg) for arg in get_args(annotation))


class UnknownNamelistKeyWarning(UserWarning):
    """A namelist dict contained keys that the schema does not know and ignored."""


class RepeatedNamelistGroupWarning(UserWarning):
    """A namelist group occurred more than once and julesconf models it once.

    Fortran allows a namelist group to be repeated within one file, and JULES
    relies on it: `jules_output_profile` occurs `nprofiles` times,
    `jules_prescribed_dataset` occurs `n_datasets` times, and
    `jules_deposition_species` occurs `ndry_dep_species` times. julesconf's
    schemas model exactly one of each, so the repetitions cannot be
    represented and are dropped — a read-then-write cycle silently loses every
    profile but the one JULES would read first.

    Distinct from `UnknownNamelistKeyWarning`, which concerns a member
    julesconf has never heard of, and from `PostponedNamelistWarning`, which
    concerns a whole namelist file julesconf deliberately excludes. This
    concerns a group julesconf *does* model but can only hold one of, so it is
    a modelling gap rather than a version gap, and is escalated separately:

        import warnings

        from julesconf.schemas import RepeatedNamelistGroupWarning

        warnings.simplefilter("error", RepeatedNamelistGroupWarning)

    Modelling these groups as lists of blocks is deferred; see `AGENTS.md`.
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
            " so the repeated groups are dropped and would be lost by a"
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
        """Names of fields that accept a list, cached per class."""
        return frozenset(
            name
            for name, info in cls.model_fields.items()
            if _is_list_annotation(info.annotation)
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
        else:
            yield path, name, info
