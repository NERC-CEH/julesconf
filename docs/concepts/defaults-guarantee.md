---
icon: lucide/shield-check
---

# The explicit-defaults guarantee

Writing namelists is deliberately **not** the inverse of reading them. Every field
julesconf holds a default for is written explicitly, whether or not you set it, so
the namelists on disk fully determine the run rather than leaning on JULES's
internal defaults. A read-then-write of a sparse config produces a larger,
self-describing one.

This is the direct fix for the
["defaults are invisible"](why-not-namelists.md#defaults-are-invisible-and-unverified)
problem: the written config becomes a full record of the run, and the gap between
the user guide and the model becomes a testable claim rather than an assumption.

## What the guarantee actually is

The honest statement is *every parameter julesconf has a default for* — not every
parameter.

A field whose default is `None` means "julesconf has no value for this", and is
omitted from the output; for those, JULES still falls back to its own internal
default. `None` is not the same as "JULES has no value for this", and that is the
crack the goal falls through. Closing it is ongoing work.

So the guarantee holds fully for every parameter julesconf carries a default for,
and the [coverage page](coverage.md) is where to look for how much of the
documented surface that currently is.

## Per-element defaults

Some JULES defaults apply *per element* of a runtime-sized list — `use_file`
defaults to `T` for every variable, `cansnowpft` to `F` for every PFT. Writing a
single value would be wrong: Fortran namelist input is positional, so `use_file =
T` sets element 1 only and leaves the rest to whatever JULES initialised them to.

julesconf therefore expands these to the full list length at write time, so the
namelist is explicit, while leaving your TOML terse. The marker that drives this
is `PerElementDefault` (see [field constraints](../api/schemas/constraints.md)).
