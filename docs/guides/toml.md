# TOML configuration


## Converting an existing config to TOML

...


## Generating JULES native configs from TOML

## Authoring a config in TOML (old)

TOML is the format recommended for new projects: a single readable file, where you
write only what you set. This tutorial builds one up and writes the namelists JULES
consumes. It assumes you have done [Get started](get-started.md).

We will start from the migrated Loobos example and make it our own.

### Start from a real config

`examples/loobos/loobos.toml` is the Loobos flux-tower run, migrated to
[grouped TOML](../api/schemas/grouped.md). Copy it to `config.toml` and open it —
it is a good map of what a full config contains.

Load it to confirm it validates:

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")
```

### Change a scalar parameter

Most parameters are plain TOML keys under a block table. To use an hourly timestep,
edit `timesteps` in the file:

```toml
[timesteps.jules_time]
timestep_len = 3600
```

Enum-valued options are written by **name**, not number:

```toml
[jules_soil.jules_soil]
soilhc_method = "johansen"
```

The [option values](../api/schemas/enums.md) reference lists the valid names for
every enum field.

### Add a plant functional type

This is where the grouped form earns its keep. Each surface type is one table, and
you never touch `npft` — julesconf counts it from your entries. Append a `[[pft]]`:

```toml
[[pft]]
name = "needleleaf"
type = "ndl_leaf"
canht_ft = 17.0
lai = 4.0
neff = 0.9e-3
# … the same parameters every other [[pft]] sets
```

Every `[[pft]]` must set the same parameters — a namelist array cannot be partially
specified, and julesconf tells you exactly which line is missing one if you slip.
The full walkthrough, including crop and non-vegetated types, is in
[add a plant functional type](../how-to/add-a-pft.md).

### Validate and write the namelists

Re-read to validate your edits, then write the namelists JULES will run:

```python
config = JulesNamelists.from_toml("config.toml")
config.to_namelists("run/namelists")
```

Open the written `run/namelists/pft_params.nml`: your one `[[pft]]` table has been
pivoted back into the parallel arrays at the right index, and every parameter
julesconf holds a default for is stated explicitly. Your TOML stayed terse; the
namelists are complete.

### What you learned

- New configs live comfortably in one grouped TOML file.
- Surface types are named tables — adding one is a single edit, and length
  mismatches are not expressible.
- `to_namelists` expands the terse config into the complete, explicit namelists JULES consumes.


## Migrate a legacy config to TOML

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

### A worked example

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

### Round-tripping back to namelists

TOML is a lossless intermediate for everything julesconf models, so you can go
back:

```python
JulesNamelists.from_toml("config.toml").to_namelists("run/namelists-new")
```

The written namelists will be **larger** than the originals — every parameter
julesconf holds a default for is stated explicitly (see
[the explicit-defaults guarantee](../concepts/defaults-guarantee.md)).

### Watch for dropped members

If your namelists contain members julesconf does not model, they are ignored on
read and would not survive the round-trip. That is usually fine for migration, but
if you need to know, migrate under [strict validation](strict-validation.md) so an
unknown member raises instead of being silently dropped.

### When to keep the flat form

One case does not round-trip cleanly through the grouped form: a TRIFFID array
supplied at the tolerated `npft` length (rather than `nnpft`). The grouped form
truncates the trailing unread values and warns
([`ToleratedLengthWarning`](../api/schemas/warnings.md)). To preserve those bytes,
write the flat form instead:

```python
JulesNamelists.from_namelists("run/namelists").to_toml("config.toml", grouped=False)
```
