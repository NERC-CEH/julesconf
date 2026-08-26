---
icon: lucide/file-code
---

# Working with namelists

JULES reads its configuration from 29 Fortran namelist files.
julesconf treats that directory as a first-class format: it reads one, validates it, lets you edit parameters as typed Python attributes, and writes it back.
Nothing here requires TOML.

## Read and validate a directory

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_namelists("run/namelists")
```

Validation happens on the read.
Types, bounds, enum values, list lengths against `npft` and its siblings, and the consistency rules that span namelists all run before you get an object back.
An invalid config raises `pydantic.ValidationError`.

The same check without Python:

```sh
julesconf validate run/namelists
```

Failures are reported the way JULES names things — file, namelist group, member — rather than by position in the model tree:

```
Validation failed (2 errors):

  jules_soil.nml  JULES_SOIL  dzsoil_io
    dzsoil_io has 3 element(s), expected sm_levels=4

  jules_vegetation.nml  JULES_VEGETATION  can_rad_mod
    7 is not a valid value; valid values: 1, 2, 3, 4, 5, 6
```

## Validate one file at a time

Sometimes you are editing `jules_soil.nml` and want to know it is well-formed before assembling the rest of the run.
Point the same command at the file:

```sh
julesconf validate run/namelists/jules_soil.nml
```

or, in Python:

```python
block = JulesNamelists.from_namelist_file("run/namelists/jules_soil.nml")
```

This is a faster, weaker check, and every run says so.
It applies that file's own types, bounds and enums, plus any rule whose inputs all live in the same file.
It cannot check the list lengths tied to `npft`, `ncpft`, `nnvg` and `ntype`, because those dimensions are declared in `jules_surface_types.nml`, and it cannot check rules that read switches from more than one file.
A file passing here can still be rejected by `from_namelists`, so validate the directory before you trust the config.

The argument has to be one of the 29 files julesconf models.
Anything else is a usage error and exits `2`.

## Edit a parameter

The model is an ordinary Pydantic object, one attribute per namelist and one per member:

```python
config.timesteps.jules_time.timestep_len = 3600
```

Assignment itself is **not** validated — Pydantic only checks on construction, and `validate_assignment` is off here because the cross-namelist rules would then run on every attribute you touch.
So after editing, re-validate before you write:

```python
JulesNamelists.model_validate(config.to_namelist_dict())
```

Setting `timestep_len = 0` sticks silently; the re-validation is what rejects it.

## Write it back out

```python
config.to_namelists("run/namelists-new")
```

Pass `overwrite_ok=True` to write over existing `.nml` files.

### Every default is written explicitly

The written namelists will be **larger** than the ones you read.
This is deliberate, and it is the main reason to put julesconf in front of a JULES run.

Omit a member from a namelist and JULES substitutes an internal default.
What that default is, and whether it matches the user guide, cannot be told from the config — you have to read the Fortran.
So a config that "works" may be relying on a documented default the model does not actually apply.

julesconf writes every member it holds a default for, whether or not you set it.
The namelists on disk then fully determine the run, and the gap between the user guide and the model becomes a testable claim rather than an assumption.

The honest statement of the guarantee is *every parameter julesconf has a default for*, not every parameter.
A field whose default is `None` means julesconf has no value for it, and it is omitted from the output; JULES still falls back to its own internal default there.
Which fields those are is a moving target — see [coverage and versions](../reference/coverage.md).

### Per-element defaults

Some JULES defaults apply per element of a runtime-sized list: `use_file` defaults to `T` for every variable, `cansnowpft` to `F` for every PFT.
Writing a single value would be wrong, because Fortran namelist input is positional — `use_file = T` sets element 1 and leaves the rest at whatever JULES initialised them to.

julesconf expands these to the full list length at write time.
The marker that drives it is `PerElementDefault`, documented with the rest of the [field constraints](../reference/api/constraints.md).

## Members julesconf does not model

By default an unrecognised namelist member is ignored, with an `UnknownNamelistKeyWarning` per key.
That is the right call for reading a config from a different JULES version, where the warnings are a map of what that version has and v7.9 did not.

It is the wrong call on a path headed for `to_namelists`, where an ignored member would be silently dropped.
Pass `strict=True` to promote the warning to an error:

```python
JulesNamelists.from_namelists("run/namelists", strict=True)
```

`--strict` does the same on the command line.

To escalate one situation and not the others, use the standard `warnings` machinery — each has its own class:

```python
import warnings
from julesconf.schemas import PostponedNamelistWarning

warnings.simplefilter("error", PostponedNamelistWarning)
```

[Warnings and errors](../reference/warnings.md) lists every class and what triggers it.

## Reading the warnings

The CLI groups warnings by class and sorts them by consequence rather than printing them in arrival order.
Each class sits in one of two bands.

**Data loss** means part of the configuration cannot be represented and is being dropped, so writing it back out would lose it.
`UnknownNamelistKeyWarning`, `RepeatedNamelistGroupWarning` and `PostponedNamelistWarning` are in this band.

**Advisory** means the configuration is representable, but something in it is probably not what its author intended — `InactiveNamelistKeyWarning` for a member JULES will never read given the switches elsewhere, `DiscouragedValueWarning` for a value the JULES developers advise against.

`--quiet` suppresses the advisory band and the success line.
The data-loss band is always shown.

## Next

- The data files that sit alongside the namelists: [data files](data-files.md).
- The same configuration as one readable file: [working with TOML](toml.md).
