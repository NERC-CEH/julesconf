# Grouped configuration

JULES parameterises surface types with parallel arrays spread across five namelist files.
Configuring one plant functional type means editing 78 separate list members, each of which must have the right length and put its value at the right index — and nothing in the config records that element 3 of `canht_ft_io` and element 3 of `g_area_io` describe the same thing.

The grouped TOML form pivots those arrays so that each surface type is one table:

```toml
[[pft]]
name = "broadleaf"
type = "brd_leaf"
canht_ft = 19.01
lai = 5.0

[[crop_pft]]
name = "maize"
type = "c4_crop"
canht_ft = 2.0
t_bse = 294.0

[[nvg]]
name = "urban"
type = "urban"
albsnc_nvg = 0.4
```

This is what `to_toml` writes by default, and `from_toml` detects it automatically.
Pass `grouped=False` for the flat form that mirrors the namelists one-to-one.

## What the grouped form removes

`npft`, `ncpft` and `nnvg` are no longer written — they are the lengths of the three arrays.
Neither are the `jules_surface_types` index members (`brd_leaf = 1`, `c3_grass = 3`, …): each entry's `type` key plus its position reconstructs them.
A whole class of error disappears with them, because a length mismatch is no longer expressible.

Five tables vanish from the config entirely: `pft_params`, `nveg_params`, `crop_params`, `triffid_params` and `jules_surface_types`.

## Which parameters go where

Membership follows the dimension a parameter is declared with, so the split is structural rather than conventional:

| Group | Carries | Meaning |
|---|---|---|
| `[[pft]]` | `npft`, `nnpft`, `ntype` | Natural PFTs. TRIFFID parameters (`nnpft`) appear here only, because TRIFFID models natural vegetation dynamics. |
| `[[crop_pft]]` | `npft`, `ncpft`, `ntype` | Crop PFTs. Crop parameters (`ncpft`) appear here only. |
| `[[nvg]]` | `nnvg`, `ntype` | Non-vegetated surface types. |

Ordering is semantic, not cosmetic: JULES requires vegetated surfaces first, with crop PFTs in the trailing PFT positions.
The assembler emits `[[pft]]` entries, then `[[crop_pft]]`, then `[[nvg]]`, so the position of an entry in the file *is* its surface type index.

## All-or-none specification

A Fortran namelist array cannot be partially specified — there is no way to omit element 3. Each parameter must therefore be given by every entry that contributes to its dimension, or by none of them:

```
a namelist array cannot be partially specified:
  pft[2] ('c3_grass') omits 'neff' but pft[0] ('broadleaf') sets it
```

This replaces a length-mismatch error with one that names the line to edit.

## Entry models

`Pft`, `CropPft` and `Nvg` are generated from the `ListLen` metadata on the flat schemas rather than hand-written, so bounds, validators and field documentation carry over automatically and a new `ListLen` field appears in the grouped form with no further work.

::: julesconf.schemas._grouped
    options:
      members:
        - Pft
        - CropPft
        - Nvg
        - GroupedConfigError
        - ToleratedLengthWarning
        - is_grouped
        - assemble
        - disassemble
