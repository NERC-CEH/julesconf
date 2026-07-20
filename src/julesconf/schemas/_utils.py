"""Shared utilities for schema field definitions."""

import dataclasses
from enum import IntEnum
from typing import Annotated

from pydantic import BeforeValidator, Field

__all__ = [
    "Fraction",
    "ListLen",
    "NonNegFloat",
    "SentinelOrFraction",
    "SentinelOrNonNegFloat",
    "SentinelOrZeroOne",
    "ZeroOne",
    "name_or_value",
]


@dataclasses.dataclass(frozen=True)
class ListLen:
    """Metadata marking a list field as requiring a specific cross-namelist length.

    Attributes:
        dim: The dimension name, e.g. ``"npft"``, ``"nnvg"``, ``"ncpft"``,
            ``"ntype"``. Resolved against ``jules_surface_types`` at validation
            time in :class:`~julesconf.schemas.namelists.JulesNamelists`.
    """

    dim: str


ZeroOne = Annotated[int, Field(ge=0, le=1)]
"""Integer restricted to ``0`` or ``1`` (e.g. binary flags)."""

Fraction = Annotated[float, Field(ge=0.0, le=1.0)]
"""Float restricted to the ``[0.0, 1.0]`` interval (e.g. albedo, emissivity)."""

NonNegFloat = Annotated[float, Field(ge=0.0)]
"""Float restricted to non-negative values."""


def _sentinel_or_fraction(v):
    """Accept ``-1.0`` (JULES sentinel for "use default") or a value in ``[0.0, 1.0]``."""
    if v == -1.0:
        return v
    if not (0.0 <= v <= 1.0):
        raise ValueError("Expected -1.0 (sentinel) or a value in [0.0, 1.0]")
    return v


SentinelOrFraction = Annotated[float, BeforeValidator(_sentinel_or_fraction)]
"""Float restricted to ``[0.0, 1.0]`` or the JULES sentinel ``-1.0``."""


def _sentinel_or_non_neg(v):
    """Accept ``-1.0`` (JULES sentinel) or a non-negative value."""
    if v == -1.0:
        return v
    if v < 0.0:
        raise ValueError("Expected -1.0 (sentinel) or a non-negative value")
    return v


SentinelOrNonNegFloat = Annotated[float, BeforeValidator(_sentinel_or_non_neg)]
"""Float restricted to ``>= 0.0`` or the JULES sentinel ``-1.0``."""


def _sentinel_or_zero_one(v):
    """Accept ``-1`` (JULES sentinel) or ``0``/``1``."""
    if v == -1:
        return v
    if v not in (0, 1):
        raise ValueError("Expected -1 (sentinel) or 0 or 1")
    return v


SentinelOrZeroOne = Annotated[int, BeforeValidator(_sentinel_or_zero_one)]
"""Integer restricted to ``0`` or ``1``, or the JULES sentinel ``-1``."""


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
