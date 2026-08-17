# Config validation


## Validate a single namelist

Sometimes you only have one namelist block, not a whole directory. Each `.nml`
file has its own model you can validate in isolation.

### Validate one block

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

### What single-file validation cannot check

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

## Enforce strict validation

By default julesconf **ignores** namelist members it does not model, emitting an
`UnknownNamelistKeyWarning` per unknown key rather than failing. That is the right
call for reading a config from a different JULES version — but on a path destined
for `to_namelists`, those members would be silently dropped.

### Turn unknown keys into errors

Pass `strict=True` on either read method to promote the warning to an error:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists", strict=True)
JulesNamelists.from_toml("config.toml", strict=True)
```

### Escalate a specific warning class

There are distinct warning classes, so you can escalate them independently with the
standard `warnings` machinery. For example, to fail only when a
[postponed namelist](../concepts/coverage.md#deliberately-out-of-scope-postponed-namelists)
is present, while leaving unknown-key warnings as warnings:

```python
import warnings
from julesconf.schemas import PostponedNamelistWarning

warnings.simplefilter("error", PostponedNamelistWarning)
```

The [warnings and errors](../api/schemas/warnings.md) reference lists every class,
what triggers it, and what it means.

### When to use which

- **Reading a config you intend to edit and re-emit** — use `strict=True`, so a
  parameter julesconf cannot preserve is a hard failure rather than silent data
  loss.
- **Reading a config from another JULES version to inspect** — leave the defaults,
  and read the warnings as a map of what this version has that v7.9 did not.
