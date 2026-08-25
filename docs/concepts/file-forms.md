---
icon: lucide/file-text
---

# The two file forms

julesconf works with a JULES configuration in two file forms, and lets you move
freely between them. Both are first-class: namelists are the format JULES itself
consumes, and TOML is the terser form recommended for new projects.

- **Namelists** — the 29 Fortran `.nml` files JULES reads. Verbose, spread across
  a directory, and the format JULES requires.
- **TOML** — a single readable file. Terse (you write only what you set), with a
  [grouped form](../api/schemas/grouped.md) that collapses the parallel
  per-surface-type arrays into named tables.

Both are validated by the same
[`JulesNamelists`](../api/schemas/namelists.md) model, so whichever you read, you
get the same checked configuration and can write out either.

## The four methods

The two formats are peers. `JulesNamelists` exposes a symmetric read/write method
for each:

| Direction | Namelists | TOML |
|---|---|---|
| **Read** (→ `JulesNamelists`) | `from_namelists(dir)` | `from_toml(path)` |
| **Write** (from `JulesNamelists`) | `to_namelists(dir)` | `to_toml(path)` |

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_namelists("run/namelists")  # read what JULES consumes
config.to_toml("config.toml")  # write the readable form
```

Any read pairs with any write, so all four combinations are valid — including the
two that convert between formats (see
[migrating a legacy config](../how-to/migrate-to-toml.md)).

## Reading and writing TOML

`from_toml` auto-detects the file's form — flat (mirroring the namelists
one-to-one) or [grouped](../api/schemas/grouped.md) — so you do not have to
declare which you wrote.

`to_toml` writes the **grouped form by default**, because it is the one that
removes the parallel-array editing burden. Pass `grouped=False` for the flat form:

```python
config.to_toml("config.toml")  # grouped [[pft]] / [[nvg]] / ...
config.to_toml("flat.toml", grouped=False)  # one table per namelist block
```

## Flat versus grouped TOML

The **flat** form is a direct transcription of the namelists: one TOML table per
block, the same member names, the same parallel arrays. The **grouped** form
pivots the per-surface-type arrays so each PFT or non-vegetated type is a single
entry, and derives `npft` / `ncpft` / `nnvg` from how many entries you write. The
[grouped configuration](../api/schemas/grouped.md) page covers the pivot, the
natural/crop ordering, and the all-or-none rule in full.

Keep the flat form when you need to preserve a TRIFFID array supplied at the
tolerated `npft` length — the grouped form truncates the trailing unread values
and warns (`ToleratedLengthWarning`, see [warnings](../api/schemas/warnings.md)).
For everything else, grouped is the default for a reason.

## Enums are names in TOML, integers in namelists

Enum-valued fields are written as their **names** in TOML (`soilhc_method =
"johansen"`) and as plain **integers** in namelists, which is what each format
reads back cleanly. On input, either form accepts a name or its integer value.
The full vocabulary is on the [option values](../api/schemas/enums.md) page.
