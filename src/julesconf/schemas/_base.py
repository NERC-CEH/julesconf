"""Shared base model for JULES namelist schemas."""

import warnings
from functools import cache
from typing import Any, get_args, get_origin

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["NamelistModel", "UnknownNamelistKeyWarning"]


def _is_list_annotation(annotation: Any) -> bool:
    """Return whether an annotation admits a list, looking through unions.

    Handles `list[X]`, `list[X] | None` and `Annotated[list[X] | None, ...]`.
    """
    if get_origin(annotation) is list:
        return True
    return any(_is_list_annotation(arg) for arg in get_args(annotation))


class UnknownNamelistKeyWarning(UserWarning):
    """A namelist dict contained keys that the schema does not know and ignored."""


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

    model_config = ConfigDict(extra="ignore")

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
            for key in sorted(set(data) - set(cls.model_fields)):
                warnings.warn(
                    f"{cls.__name__}: ignoring unknown namelist member {key!r}",
                    UnknownNamelistKeyWarning,
                    stacklevel=2,
                )
        return data
