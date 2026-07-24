---
icon: lucide/shield-alert
---

# Enforce strict validation

By default julesconf **ignores** namelist members it does not model, emitting an
`UnknownNamelistKeyWarning` per unknown key rather than failing. That is the right
call for reading a config from a different JULES version — but on a path destined
for `to_namelists`, those members would be silently dropped.

## Turn unknown keys into errors

Pass `strict=True` on either read method to promote the warning to an error:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists", strict=True)
JulesNamelists.from_toml("config.toml", strict=True)
```

## Escalate a specific warning class

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

## When to use which

- **Reading a config you intend to edit and re-emit** — use `strict=True`, so a
  parameter julesconf cannot preserve is a hard failure rather than silent data
  loss.
- **Reading a config from another JULES version to inspect** — leave the defaults,
  and read the warnings as a map of what this version has that v7.9 did not.
