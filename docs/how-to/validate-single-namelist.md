---
icon: lucide/file-check
---

# Validate a single namelist

Sometimes you only have one namelist block, not a whole directory. Each `.nml`
file has its own model you can validate in isolation.

## Validate one block

Read the file and validate the block against its model:

```python
from julesconf.config import NamelistFileHandler
from julesconf.schemas.timesteps import TimestepsNamelist

data = NamelistFileHandler().read("run/namelists/timesteps.nml")
TimestepsNamelist.model_validate(data["timesteps"])
```

Every namelist module exposes a top-level model named after the file
(`TimestepsNamelist` for `timesteps.nml`, and so on) — see the
[schemas overview](../api/schemas/index.md) for the full list.

## What single-file validation cannot check

Per-file validation checks that block's own bounds, enums and types, but **not**
list lengths tied to `npft` / `nnvg` / `ncpft` / `ntype`. Those dimensions are
declared in `jules_surface_types.nml`, so the cross-namelist checks live on the
whole-directory model,
[`JulesNamelists`](../api/schemas/namelists.md), not on the per-file model.

If you need the length checks, validate the whole directory instead:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists")
```
