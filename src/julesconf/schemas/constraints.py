"""Reusable field constraints for JULES namelist schemas.

These are the building blocks the per-namelist modules annotate their fields
with: constrained scalar types (`Fraction`, `NonNegFloat`, …), the `ListLen`
marker for cross-namelist list dimensions, and the `name_or_value` helper for
enum fields. They are the vocabulary to reach for when adding a schema for a
namelist that does not have one yet.
"""

import dataclasses
from enum import IntEnum
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field

__all__ = [
    "LIST_LEN_DIMS",
    "PER_ELEMENT_DIMS",
    "Fraction",
    "ListLen",
    "NonNegFloat",
    "PerElementDefault",
    "SentinelOrFraction",
    "ZeroOne",
    "name_or_value",
]

LIST_LEN_DIMS = frozenset({"npft", "nnvg", "ncpft", "ntype"})
"""Dimension names `ListLen` may refer to.

`julesconf.schemas.JulesNamelists` resolves each of these against
`jules_surface_types` when checking list lengths.
"""

SIBLING_DIMS = frozenset({"nvars"})
"""Dimension names resolved from a sibling field on the same model.

Unlike `LIST_LEN_DIMS`, which are global and read from `jules_surface_types`,
these name a field in the *same* namelist block (e.g. `nvars` in
`JULES_SOIL_PROPS`). Each block carries its own value.
"""

PER_ELEMENT_DIMS = LIST_LEN_DIMS | SIBLING_DIMS
"""Dimension names `PerElementDefault` may refer to."""


@dataclasses.dataclass(frozen=True)
class ListLen:
    """Metadata marking a list field as requiring a specific cross-namelist length.

    Attributes:
        dim: The dimension name, which must be a member of `LIST_LEN_DIMS`.
            Resolved against `jules_surface_types` at validation time in
            `julesconf.schemas.JulesNamelists`.
    """

    dim: str

    def __post_init__(self) -> None:
        """Reject dimension names that no schema can resolve."""
        if self.dim not in LIST_LEN_DIMS:
            raise ValueError(
                f"Unknown ListLen dim {self.dim!r}; "
                f"expected one of {sorted(LIST_LEN_DIMS)}"
            )


@dataclasses.dataclass(frozen=True)
class PerElementDefault:
    """Metadata marking a list field whose JULES default applies to every element.

    Several JULES list parameters document a scalar default meaning "this value
    for every element" — `use_file` defaults to `T`, `var_name` to `''`. The
    element count is not known until the rest of the config is validated, so the
    value cannot be expressed as an ordinary Pydantic default.

    Fortran namelist input assigns array values positionally and does **not**
    broadcast a scalar across an array: writing `use_file = T` for a
    `logical(nvars)` sets element 1 only, leaving the rest at whatever the JULES
    source initialised them to. Fields carrying this marker are therefore
    expanded to their full length when writing namelists, so the written config
    fully determines the run.

    Expansion happens at *write* time, not validation time, so a TOML config
    stays terse while the namelists it produces stay explicit.

    Attributes:
        value: The scalar value to repeat for every element.
        dim: The dimension giving the element count. Members of `LIST_LEN_DIMS`
            resolve globally against `jules_surface_types`; members of
            `SIBLING_DIMS` resolve against a field of that name on the same
            model.
    """

    value: Any
    dim: str

    def __post_init__(self) -> None:
        """Reject dimension names that no schema can resolve."""
        if self.dim not in PER_ELEMENT_DIMS:
            raise ValueError(
                f"Unknown PerElementDefault dim {self.dim!r}; "
                f"expected one of {sorted(PER_ELEMENT_DIMS)}"
            )


ZeroOne = Annotated[int, Field(ge=0, le=1)]
"""Integer restricted to `0` or `1` (e.g. binary flags)."""

Fraction = Annotated[float, Field(ge=0.0, le=1.0)]
"""Float restricted to the `[0.0, 1.0]` interval (e.g. albedo, emissivity)."""

NonNegFloat = Annotated[float, Field(ge=0.0)]
"""Float restricted to non-negative values."""


def _sentinel_or_fraction(v: float) -> float:
    """Accept `-1.0` (JULES sentinel for "use default") or a value in `[0.0, 1.0]`."""
    if v == -1.0:
        return v
    if not (0.0 <= v <= 1.0):
        raise ValueError("Expected -1.0 (sentinel) or a value in [0.0, 1.0]")
    return v


SentinelOrFraction = Annotated[float, AfterValidator(_sentinel_or_fraction)]
"""Float restricted to `[0.0, 1.0]` or the JULES sentinel `-1.0`.

Runs *after* Pydantic's float coercion, so non-numeric input yields a normal
`ValidationError` rather than a `TypeError` from the range comparison.
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
