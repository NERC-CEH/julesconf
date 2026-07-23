---
icon: lucide/rocket
---

# julesconf

More robust tooling for JULES configurations. Configure a JULES run from a
single readable TOML file, and let julesconf write the 29 Fortran namelist
files that the model actually consumes.

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")
config.to_namelists("/path/to/jules/namelists")
```

## Why not just write the namelists?

A JULES run is configured through 29 Fortran namelist files. That format has
three properties that make it hard to author correctly, and julesconf is
positioned to fix all three.

**Defaults are invisible and unverified.** Omit a namelist member and JULES
substitutes an internal default. What that default is, and whether it matches
the user guide, cannot be told from the config — you have to read the Fortran.
julesconf inverts this: you write only what you care about, and it writes
namelists that state every parameter it holds a default for, so the written
config determines the run rather than a partial record of it.

**Related parameters are scattered across files.** Configuring one plant
functional type means editing dozens of parallel list fields spread over
`pft_params.nml`, `triffid_params.nml`, `jules_snow.nml` and `crop_params.nml`,
each of which must have the same length in the same order. julesconf's
[grouped form](api/schemas/grouped.md) pivots those arrays so each surface type
is one named object, and a length mismatch is no longer even expressible.

**Position is the only identity.** A PFT is an index — nothing in the config
records that element 3 of `canht_ft_io` and element 3 of `g_area_io` describe
the same thing. The grouped form makes each surface type an entry keyed by
`type`, so identity is explicit rather than conventional.

## Where next

- **[Configuration guide](guide/configuration.md)** — the two file forms, the
  defaults guarantee, migrating a legacy config, and strict validation.
- **[Grouped configuration](api/schemas/grouped.md)** — the `[[pft]]` /
  `[[crop_pft]]` / `[[nvg]]` arrays of tables in detail.
- **[API reference](api/schemas/namelists.md)** — `JulesNamelists` and the
  per-namelist schemas.
