"""Shared utilities for schema field definitions."""

import dataclasses
from enum import IntEnum
from typing import Annotated, Any, get_args

from pydantic import AfterValidator, BeforeValidator, Field
from pydantic.fields import FieldInfo

__all__ = [
    "LIST_LEN_DIMS",
    "Fraction",
    "ListLen",
    "NonNegFloat",
    "SentinelOrFraction",
    "ZeroOne",
    "find_list_len",
    "name_or_value",
]

LIST_LEN_DIMS = frozenset({"npft", "nnvg", "ncpft", "ntype"})
"""Dimension names :class:`ListLen` may refer to.

:class:`~julesconf.schemas.namelists.JulesNamelists` resolves each of these
against ``jules_surface_types`` when checking list lengths.
"""


@dataclasses.dataclass(frozen=True)
class ListLen:
    """Metadata marking a list field as requiring a specific cross-namelist length.

    Attributes:
        dim: The dimension name, which must be a member of :data:`LIST_LEN_DIMS`.
            Resolved against ``jules_surface_types`` at validation time in
            :class:`~julesconf.schemas.namelists.JulesNamelists`.
    """

    dim: str

    def __post_init__(self) -> None:
        """Reject dimension names that no schema can resolve."""
        if self.dim not in LIST_LEN_DIMS:
            raise ValueError(
                f"Unknown ListLen dim {self.dim!r}; "
                f"expected one of {sorted(LIST_LEN_DIMS)}"
            )


def find_list_len(field_info: FieldInfo) -> ListLen | None:
    """Return the :class:`ListLen` metadata for a field, if it has any.

    Pydantic only surfaces metadata from the outermost ``Annotated`` in
    ``FieldInfo.metadata``, so ``Annotated[list[X], ListLen(...)] | None``
    hides the marker inside a union member. This searches the full annotation
    so both that spelling and the canonical
    ``Annotated[list[X] | None, ListLen(...)]`` resolve.

    Args:
        field_info: The Pydantic field to inspect.

    Returns:
        The first :class:`ListLen` found, or ``None`` if the field has none.
    """
    for meta in field_info.metadata:
        if isinstance(meta, ListLen):
            return meta
    return _find_in_annotation(field_info.annotation)


def _find_in_annotation(annotation: Any) -> ListLen | None:
    """Recursively search an annotation's type arguments for a ``ListLen``."""
    for arg in get_args(annotation):
        if isinstance(arg, ListLen):
            return arg
        found = _find_in_annotation(arg)
        if found is not None:
            return found
    return None


ZeroOne = Annotated[int, Field(ge=0, le=1)]
"""Integer restricted to ``0`` or ``1`` (e.g. binary flags)."""

Fraction = Annotated[float, Field(ge=0.0, le=1.0)]
"""Float restricted to the ``[0.0, 1.0]`` interval (e.g. albedo, emissivity)."""

NonNegFloat = Annotated[float, Field(ge=0.0)]
"""Float restricted to non-negative values."""


def _sentinel_or_fraction(v: float) -> float:
    """Accept ``-1.0`` (JULES sentinel for "use default") or a value in ``[0.0, 1.0]``."""
    if v == -1.0:
        return v
    if not (0.0 <= v <= 1.0):
        raise ValueError("Expected -1.0 (sentinel) or a value in [0.0, 1.0]")
    return v


SentinelOrFraction = Annotated[float, AfterValidator(_sentinel_or_fraction)]
"""Float restricted to ``[0.0, 1.0]`` or the JULES sentinel ``-1.0``.

Runs *after* Pydantic's float coercion, so non-numeric input yields a normal
``ValidationError`` rather than a ``TypeError`` from the range comparison.
"""


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
