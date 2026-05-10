"""Shared utilities for schema field definitions."""

from enum import IntEnum

from pydantic import BeforeValidator

__all__ = ["name_or_value"]


def name_or_value(enum_cls: type[IntEnum]) -> BeforeValidator:
    """Return a validator that accepts an IntEnum's integer value or string member name."""

    def coerce(v):
        if isinstance(v, str):
            try:
                return enum_cls[v]
            except KeyError:
                raise ValueError(
                    f"{v!r} is not a valid name; "
                    f"valid names: {[e.name for e in enum_cls]}"
                ) from None
        return v

    return BeforeValidator(coerce)
