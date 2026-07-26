---
icon: lucide/list-checks
---

# What julesconf covers

julesconf schemas **29 of the JULES namelists**, pinned to the
[JULES v7.9 user guide](https://jules-lsm.github.io/user_guide/doc/source/namelists/).
This page is the honest boundary of what is modelled, what is deliberately not,
and what that means for your config.

## Version pinning

The schemas — field names, types, bounds and defaults — track **JULES v7.9**
(`julesconf.schemas.JULES_VERSION`). A config from a different JULES version will
still read: members julesconf does not recognise produce an
`UnknownNamelistKeyWarning` rather than an error, so the format is tolerant across
versions. But the further your JULES is from v7.9, the more those warnings mean
"this version has parameters v7.9 did not", and the less julesconf can validate
them. See [warnings and errors](../api/schemas/warnings.md) for how to escalate.

## The 29 schema'd namelists

Listed with their models on the [schemas overview](../api/schemas/index.md). Each
`.nml` file maps to one module and one top-level `*Namelist` model.

## Deliberately out of scope: postponed namelists

`cable_*`, `oasis_rivers` and `red_params` have reference docs but **no schemas by
design**. They configure rarely-used JULES extensions — the CABLE land surface
scheme, OASIS river coupling, and the RED vegetation demography model — that would
add substantial modelling complexity for very few users.

This is a scoping decision, not a gap. Because a config using one of these files
is not fully supported, julesconf **warns rather than silently dropping it**: a
`PostponedNamelistWarning` fires when one is detected, so the exclusion is visible
instead of looking like support. A handful of other documented namelists (e.g.
`jules_soil_ecosse.nml`) are simply **not yet schema'd** — distinct from
postponed, and candidates for a future contribution using the
[field constraints](../api/schemas/constraints.md).

## The `None`-defaults caveat

Within the 29 schema'd namelists, not every field carries a default. Fields that
default to `None` are omitted on write, and JULES falls back to its own internal
default for them. This is the boundary discussed in
[the explicit-defaults guarantee](defaults-guarantee.md): the guarantee is airtight
for every parameter julesconf has a default for, and these are the ones still
outside it.

## Unknown members within a modelled namelist

Even in a namelist julesconf *does* model, an unrecognised member (a typo, or a
parameter from another version) is ignored with an `UnknownNamelistKeyWarning`
rather than rejected. That is the right call for reading — but on a path headed for
`to_namelists`, an ignored member would be silently dropped. Pass `strict=True` to
turn the warning into an error; see
[enforce strict validation](../how-to/strict-validation.md).
