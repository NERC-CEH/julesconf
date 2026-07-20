"""Shared base model for JULES namelist schemas."""

import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["NamelistModel", "UnknownNamelistKeyWarning"]


class UnknownNamelistKeyWarning(UserWarning):
    """A namelist dict contained keys that the schema does not know and ignored."""


class NamelistModel(BaseModel):
    """Base model for JULES namelist schemas that warns on unknown keys.

    Unknown keys are ignored (``extra="ignore"``) so that configs containing
    members not covered by the schema (e.g. from a different JULES version,
    or gaps in the documentation the schemas were derived from) still
    validate. However, unknown keys are frequently misspellings of real
    members, which JULES itself silently drops, so a
    :class:`UnknownNamelistKeyWarning` is emitted for each one.

    To treat unknown keys as validation errors, escalate the warning::

        import warnings

        from julesconf.schemas import UnknownNamelistKeyWarning

        warnings.simplefilter("error", UnknownNamelistKeyWarning)
    """

    model_config = ConfigDict(extra="ignore")

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
