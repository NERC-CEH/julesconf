---
icon: lucide/arrow-right-left
---

# Migrate a legacy config to TOML

You have an existing directory of JULES namelists and want the single readable
[TOML file](../concepts/file-forms.md) instead. Read the namelists and write them
straight back out as TOML:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists").to_toml("config.toml")
```

That is the whole migration. `to_toml` writes the
[grouped form](../api/schemas/grouped.md) by default, so the per-surface-type
arrays come out as `[[pft]]` / `[[crop_pft]]` / `[[nvg]]` tables.

## A worked example

`examples/loobos/loobos.toml` is exactly this: the real Loobos flux-tower
configuration, migrated from its 29 namelist files. It has no crop PFTs (`ncpft =
0`), so it shows `[[pft]]` and `[[nvg]]` entries but no `[[crop_pft]]`. A crop
entry looks like:

```toml
[[crop_pft]]
name = "maize"
type = "c4_crop"
canht_ft = 2.0
t_bse = 294.0
```

## Round-tripping back to namelists

TOML is a lossless intermediate for everything julesconf models, so you can go
back:

```python
JulesNamelists.from_toml("config.toml").to_namelists("run/namelists-new")
```

The written namelists will be **larger** than the originals — every parameter
julesconf holds a default for is stated explicitly (see
[the explicit-defaults guarantee](../concepts/defaults-guarantee.md)).

## Watch for dropped members

If your namelists contain members julesconf does not model, they are ignored on
read and would not survive the round-trip. That is usually fine for migration, but
if you need to know, migrate under [strict validation](strict-validation.md) so an
unknown member raises instead of being silently dropped.

## When to keep the flat form

One case does not round-trip cleanly through the grouped form: a TRIFFID array
supplied at the tolerated `npft` length (rather than `nnpft`). The grouped form
truncates the trailing unread values and warns
([`ToleratedLengthWarning`](../api/schemas/warnings.md)). To preserve those bytes,
write the flat form instead:

```python
JulesNamelists.from_namelists("run/namelists").to_toml("config.toml", grouped=False)
```
