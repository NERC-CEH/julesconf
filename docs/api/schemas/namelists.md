# `JulesNamelists`

The top-level model, combining all 29 namelist files. Validate a complete
namelists directory with it:

```python
from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists

data = NamelistConfig().read("/path/to/jules/namelists")
model = JulesNamelists.model_validate(data)
```

As well as delegating to the per-file schemas, this model performs the checks
that no single file can make on its own — every list field carrying a
[`ListLen`](constraints.md) marker is checked against the dimension it names
(`npft`, `nnvg`, `ncpft` or `ntype`), resolved from `jules_surface_types`.

::: julesconf.schemas.JulesNamelists
