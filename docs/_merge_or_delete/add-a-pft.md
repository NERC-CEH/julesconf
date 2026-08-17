---
icon: lucide/sprout
---

# Add a plant functional type

In the namelists, adding a PFT means inserting a value at the right index in dozens
of parallel arrays across four files, and bumping `npft` everywhere. In the
[grouped TOML form](../api/schemas/grouped.md) it is **one new table**.

## Add a natural PFT

Append a `[[pft]]` entry. `npft` is the number of `[[pft]]` plus `[[crop_pft]]`
entries, so you do not set it — julesconf counts it:

```toml
[[pft]]
name = "broadleaf"
type = "brd_leaf"
canht_ft = 19.01
lai = 5.0
neff = 0.8e-3
# … the remaining npft-dimensioned parameters

[[pft]]                 # the new one
name = "needleleaf"
type = "ndl_leaf"
canht_ft = 17.0
lai = 4.0
neff = 0.9e-3
# … same parameters as above
```

## Give every entry the same parameters

A Fortran namelist array cannot be partially specified, so each parameter must be
set by **every** `[[pft]]` entry or by none of them. Omitting one from the new
entry is a clear error naming the line to fix:

```
pft[1] ('needleleaf') omits 'neff' but pft[0] ('broadleaf') sets it;
a namelist array cannot be partially specified.
```

This is the grouped form's replacement for a silent length mismatch.

## Add a crop PFT instead

Crop PFTs go in `[[crop_pft]]` and carry the crop-model (`ncpft`) parameters.
Ordering is semantic — JULES requires crop PFTs in the trailing PFT positions — so
the assembler always emits `[[pft]]` entries first, then `[[crop_pft]]`. You do not
manage the ordering; writing a `[[crop_pft]]` entry places it correctly:

```toml
[[crop_pft]]
name = "maize"
type = "c4_crop"
canht_ft = 2.0
t_bse = 294.0
# … the ncpft-dimensioned parameters
```

## Add a non-vegetated type

Same idea, in `[[nvg]]`:

```toml
[[nvg]]
name = "urban"
type = "urban"
albsnc_nvg = 0.4
# … the nnvg-dimensioned parameters
```

## Write it out

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_toml("config.toml").to_namelists("run/namelists")
```

julesconf reconstructs `npft` / `ncpft` / `nnvg`, the `jules_surface_types` index
members, and every parallel array — in the right order — from your entries. See
[grouped configuration](../api/schemas/grouped.md) for the full pivot rules.
