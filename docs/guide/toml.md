---
icon: lucide/file-text
---

# Working with TOML

A JULES configuration can also live in a single TOML file, which julesconf validates and converts to the namelists JULES consumes.
This is the form to reach for when writing a new config, for two reasons that have nothing to do with taste.

JULES parameterises surface types with parallel arrays spread across five namelist files.
Configuring one plant functional type means editing 78 separate list members, each of which has to have the right length and put its value at the right index.
And position is the only identity a surface type has: nothing in the config records that element 3 of `canht_ft_io` and element 3 of `g_area_io` describe the same plant.

The grouped TOML form pivots those arrays so each surface type is one table, which makes a length mismatch not merely detectable but inexpressible.

## Start from an existing config

The quickest way in is to convert a config you already have:

```sh
julesconf convert nml2toml run/namelists -o config.toml
```

or in Python:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists").to_toml("config.toml")
```

`examples/loobos/loobos.toml` in the repository is exactly this — the Loobos flux-tower run, converted from its 29 namelist files.
It is a good map of what a full config contains.

If your namelists contain members julesconf does not model, they are dropped rather than converted.
Convert with `--strict` if you need that to be an error instead.

## The two forms

`to_toml` writes the **grouped** form by default and `from_toml` detects which form it is reading, so you never have to declare it.

The **flat** form is a direct transcription of the namelists: one table per namelist block, the same member names, the same parallel arrays.

```toml
[timesteps.jules_time]
timestep_len = 3600
```

The **grouped** form is the flat form with the surface-type arrays pivoted:

```toml
[[pft]]
name = "broadleaf"
type = "brd_leaf"
canht_ft = 19.01
lai = 5.0

[[nvg]]
name = "urban"
type = "urban"
albsnc_nvg = 0.4
```

Five tables disappear from the config entirely — `pft_params`, `nveg_params`, `crop_params`, `triffid_params` and `jules_surface_types`.
So do `npft`, `ncpft` and `nnvg`, which are just the lengths of the three arrays, and the `jules_surface_types` index members (`brd_leaf = 1`, `c3_grass = 3`, …), which each entry's `type` key and position reconstruct.

## Set a parameter

Most parameters are plain keys under a block table:

```toml
[timesteps.jules_time]
timestep_len = 3600
```

Enum-valued options are written by **name** in TOML and as plain integers in namelists:

```toml
[jules_soil.jules_soil]
soilhc_method = "johansen"
```

On input either is accepted.
[Option values](../reference/enums.md) is the list of names every enum field takes.

## Add a surface type

Append a table.
You do not set `npft` — julesconf counts it from the entries:

```toml
[[pft]]
name = "needleleaf"
type = "ndl_leaf"
canht_ft = 17.0
lai = 4.0
neff = 0.9e-3
# … the same parameters every other [[pft]] sets
```

Crop PFTs go in `[[crop_pft]]` and carry the crop-model parameters; non-vegetated types go in `[[nvg]]`.
Ordering is semantic rather than cosmetic — JULES requires vegetated surfaces first, with crop PFTs in the trailing PFT positions — but you do not manage it.
The assembler emits `[[pft]]`, then `[[crop_pft]]`, then `[[nvg]]`, so an entry's position in the file is its surface type index.

Which group a parameter belongs to follows the dimension it is declared with:

| Group | Carries | Meaning |
|---|---|---|
| `[[pft]]` | `npft`, `nnpft`, `ntype` | Natural PFTs. TRIFFID parameters (`nnpft`) appear here only, since TRIFFID models natural vegetation dynamics. |
| `[[crop_pft]]` | `npft`, `ncpft`, `ntype` | Crop PFTs. Crop parameters (`ncpft`) appear here only. |
| `[[nvg]]` | `nnvg`, `ntype` | Non-vegetated surface types. |

### Every entry sets the same parameters

A Fortran namelist array cannot be partially specified — there is no way to omit element 3.
So each parameter has to be given by every entry contributing to its dimension, or by none of them.
Omitting one raises `GroupedConfigError`, naming the line to fix:

```
a namelist array cannot be partially specified:
  pft[2] ('c3_grass') omits 'neff' but pft[0] ('broadleaf') sets it
```

That is the grouped form's replacement for a silent length mismatch.

## Validate and write the namelists

```sh
julesconf validate config.toml
julesconf convert toml2nml config.toml -o run/namelists
```

or:

```python
JulesNamelists.from_toml("config.toml").to_namelists("run/namelists")
```

Open the written `pft_params.nml`: your `[[pft]]` tables have been pivoted back into parallel arrays at the right indices, and every parameter julesconf holds a default for is stated explicitly.
The TOML stays terse; the namelists come out complete.
See [every default is written explicitly](namelists.md#every-default-is-written-explicitly) for why.

## Canonical formatting

```sh
julesconf format config.toml --in-place
```

This rewrites a config the way julesconf writes one: enum members by name, the grouped form unless you pass `--flat`, and the block order the schemas declare.
It is a pure reformat, so running it twice gives byte-identical output.

Two safeguards, because the destination is usually the file you are editing.
The config has to validate first, and nothing is written if it does not — reformatting is not repair, and julesconf will not adjust a config until the validators pass, since that would be guesswork about scientific intent.
And a destination is always explicit: `-o` writes elsewhere, `--in-place` rewrites the input, and passing neither or both is a usage error.

## When to keep the flat form

One case does not round-trip cleanly through the grouped form.
A TRIFFID array supplied at the tolerated `npft` length rather than `nnpft` has trailing values JULES never reads, and the grouped form has nowhere to put them, so it truncates them and warns (`ToleratedLengthWarning`).
That is lossless for the model run and lossy for the bytes.
To keep them, write the flat form:

```python
JulesNamelists.from_namelists("run/namelists").to_toml("config.toml", grouped=False)
```

For everything else, grouped is the default for a reason.
