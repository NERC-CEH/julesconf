# Field constraints

The reusable building blocks the per-namelist schemas annotate their fields
with. Reach for these when adding a schema for a namelist that does not have
one yet — see the [overview](index.md#coverage) for which those are.

```python
from typing import Annotated

from julesconf.schemas import NamelistModel
from julesconf.schemas.constraints import Fraction, ListLen, NonNegFloat


class JulesExample(NamelistModel):
    """`JULES_EXAMPLE` namelist members."""

    albedo_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """One albedo per plant functional type."""
```

Note the annotation order: `ListLen` must sit on the *outermost* `Annotated`,
as above. Spelling it `Annotated[list[Fraction], ListLen("npft")] | None`
buries the marker inside a union member, where Pydantic does not surface it in
`FieldInfo.metadata`.

::: julesconf.schemas.constraints
