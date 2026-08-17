---
icon: lucide/plus-square
---

# Add a schema for a new namelist

Some documented JULES namelists are [not yet schema'd](../concepts/coverage.md)
(as distinct from the deliberately postponed ones). Adding one means writing a
`NamelistModel` subclass whose fields use the shared
[constraint vocabulary](../api/schemas/constraints.md).

## Write the model

Subclass `NamelistModel` and annotate each member with the reusable constraints:

```python
from typing import Annotated

from julesconf.schemas import NamelistModel
from julesconf.schemas.constraints import Fraction, ListLen, NonNegFloat


class JulesExample(NamelistModel):
    """`JULES_EXAMPLE` namelist members."""

    albedo_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """One albedo per plant functional type."""
```

The `"""…"""` under each field is its documentation — `NamelistModel` sets
`use_attribute_docstrings=True`, so it becomes the field description and carries
into both the API docs and the generated grouped models.

## Mind the annotation order

`ListLen` must sit on the **outermost** `Annotated`, exactly as above. Spelling it
`Annotated[list[Fraction], ListLen("npft")] | None` buries the marker inside a
union member, where Pydantic does not surface it in `FieldInfo.metadata` — and the
cross-namelist length check and the grouped form both rely on finding it there.
`test_cross_namelist.py::test_every_list_len_uses_canonical_spelling` enforces the
correct spelling.

## Follow the module conventions

- Name the module after the `.nml` file, one-to-one; export the top-level
  `*Namelist` model **and** its per-block models in `__all__`.
- Enum fields accept an int value or a string name via `name_or_value()`.
- Fields dimensioned by `npft` / `nnvg` / `ncpft` / `ntype` take a `ListLen`
  marker so they are checked by [`JulesNamelists`](../api/schemas/namelists.md) and
  appear automatically in the [grouped form](../api/schemas/grouped.md).

The [field constraints](../api/schemas/constraints.md) reference documents the full
vocabulary (`Fraction`, `NonNegFloat`, `ZeroOne`, `SentinelOrFraction`, `ListLen`,
`PerElementDefault`, `name_or_value`).

!!! note "Postponed namelists are a separate matter"

    `cable_*`, `oasis_rivers` and `red_params` are out of scope by decision, not
    for lack of a schema. Don't add schemas for them without discussing it first —
    see [what julesconf covers](../concepts/coverage.md).
