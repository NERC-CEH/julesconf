---
icon: lucide/settings
---

# Configuration guide

julesconf works with a JULES configuration in two file forms, and lets you move
between them.

- **Namelists** — the 29 Fortran `.nml` files JULES itself reads. Verbose,
  spread across a directory, and the format JULES requires.
- **TOML** — a single readable file. Terse (you write only what you set), with
  a [grouped form](../api/schemas/grouped.md) that collapses the parallel
  per-surface-type arrays into named tables.

Both are validated by the same [`JulesNamelists`](../api/schemas/namelists.md)
model, so whichever you read, you get the same checked configuration and can
write out either.

## The four methods

| Direction | Namelists | TOML |
|---|---|---|
| **Read** (→ `JulesNamelists`) | `from_namelists(dir)` | `from_toml(path)` |
| **Write** (from `JulesNamelists`) | `to_namelists(dir)` | `to_toml(path)` |

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")   # read the readable form
config.to_namelists("run/namelists")               # write what JULES consumes
```

All four are documented on the [`JulesNamelists`](../api/schemas/namelists.md)
API page.

## The explicit-defaults guarantee

Writing namelists is deliberately **not** the inverse of reading them. Every
field julesconf holds a default for is written explicitly, whether or not you
set it, so the namelists on disk fully determine the run rather than leaning on
JULES's internal defaults. A read-then-write of a sparse config produces a
larger, self-describing one.

!!! note "What the guarantee actually is"

    The honest statement is *every parameter julesconf has a default for* — not
    every parameter. A field whose default is `None` means "julesconf has no
    value for this", and is omitted from the output; for those, JULES still
    falls back to its own internal default. Closing that gap is ongoing work,
    tracked in `notes/toml_config.md`.

## Reading and writing TOML

`from_toml` auto-detects the file's form — flat (mirroring the namelists
one-to-one) or [grouped](../api/schemas/grouped.md) — so you do not have to
declare which you wrote.

`to_toml` writes the **grouped form by default**, because it is the one that
removes the parallel-array editing burden. Pass `grouped=False` for the flat
form:

```python
config.to_toml("config.toml")                 # grouped [[pft]] / [[nvg]] / ...
config.to_toml("flat.toml", grouped=False)    # one table per namelist block
```

Enum-valued fields are written as their **names** in TOML (`soilhc_method =
"johansen"`) and as plain **integers** in namelists, which is what each format
reads back cleanly. On input, `from_toml` accepts either a name or its integer
value.

## Migrating a legacy configuration

Point `from_namelists` at an existing namelists directory and write it straight
back out as TOML:

```python
JulesNamelists.from_namelists("run/namelists").to_toml("config.toml")
```

`examples/loobos/loobos.toml` is exactly this: the real Loobos flux-tower
configuration, migrated from its 29 namelist files to a single grouped TOML
file. It has no crop PFTs (`ncpft = 0`), so it shows `[[pft]]` and `[[nvg]]`
entries but no `[[crop_pft]]`. A crop entry looks like:

```toml
[[crop_pft]]
name = "maize"
type = "c4_crop"
canht_ft = 2.0
t_bse = 294.0
```

## Flat versus grouped

The flat form is a direct transcription of the namelists: one TOML table per
block, the same member names, the same parallel arrays. The grouped form pivots
the per-surface-type arrays so each PFT or non-vegetated type is a single
entry, and derives `npft` / `ncpft` / `nnvg` from how many entries you write.
The [grouped configuration](../api/schemas/grouped.md) page covers the pivot,
the natural/crop ordering, and the all-or-none rule in full.

Keep the flat form when you need to preserve a TRIFFID array supplied at the
tolerated `npft` length — the grouped form truncates the trailing unread values
and warns (`ToleratedLengthWarning`). For everything else, grouped is the
default for a reason.

## Strict validation and warnings

By default, julesconf **ignores** namelist members it does not model, emitting
an `UnknownNamelistKeyWarning` per unknown key rather than failing. That is the
right call for reading a config from a different JULES version — but on a path
destined for `to_namelists`, those members would be silently dropped. Pass
`strict=True` to turn the warning into an error:

```python
JulesNamelists.from_namelists("run/namelists", strict=True)
JulesNamelists.from_toml("config.toml", strict=True)
```

There are two distinct warning classes, so you can escalate them independently:

- **`UnknownNamelistKeyWarning`** — an unknown *member* within a namelist
  julesconf does model.
- **`PostponedNamelistWarning`** — a whole namelist that is deliberately out of
  scope: `cable_*`, `oasis_rivers` and `red_params`. These configure rarely-used
  JULES extensions and are not schema'd; a config using them is not fully
  supported, and julesconf says so rather than silently omitting the files.

Escalate either to an error with the standard `warnings` machinery:

```python
import warnings
from julesconf.schemas import PostponedNamelistWarning

warnings.simplefilter("error", PostponedNamelistWarning)
```
