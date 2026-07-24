---
icon: lucide/help-circle
---

# Why not just write the namelists?

A JULES run is configured through 29 Fortran namelist files. That format has
three properties that make it hard to author correctly, and julesconf is
positioned to fix all three. Understanding them is the quickest way to see what
julesconf is *for*.

## Defaults are invisible and unverified

Omit a namelist member and JULES substitutes an internal default. What that
default is, and whether it matches the user guide, cannot be told from the config
— you have to read the Fortran. A config that "works" may be relying on a
documented default the model does not actually apply.

julesconf inverts this. You write only what you care about, and it writes
namelists that state every parameter it holds a default for, so the written
config determines the run rather than being a partial record of it. See
[the explicit-defaults guarantee](defaults-guarantee.md) for exactly what this
does and does not promise.

## Related parameters are scattered across files

Configuring one plant functional type means editing dozens of parallel list
fields spread over `pft_params.nml`, `triffid_params.nml`, `jules_snow.nml` and
`crop_params.nml`, each of which must have the same length in the same order.

julesconf's [grouped TOML form](../api/schemas/grouped.md) pivots those arrays so
each surface type is one named object, and a length mismatch is no longer even
expressible. Adding a PFT becomes [one table](../how-to/add-a-pft.md) rather than
dozens of coordinated edits.

## Position is the only identity

A PFT is an index — nothing in the config records that element 3 of `canht_ft_io`
and element 3 of `g_area_io` describe the same thing. It is a convention enforced
by the model, invisible in the text.

The grouped form makes each surface type an entry keyed by `type`, so identity is
explicit rather than conventional.

## What this means in practice

julesconf does not replace namelists — it treats them as a
[first-class format](file-forms.md) you can read and write directly. What it adds
is a validated model in between, and a second, terser [TOML form](file-forms.md)
that fixes the three problems above by construction.

- New to julesconf? Start with the [Get started](../tutorials/get-started.md)
  tutorial.
- Want the format details? See [the two file forms](file-forms.md).
- Want the objects? See [the containers](containers.md).
