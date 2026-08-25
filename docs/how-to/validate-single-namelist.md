---
icon: lucide/file-check
---

# Validate a single namelist

Sometimes you only have one namelist file, not a whole directory — you are
editing `jules_soil.nml` and want to know whether it is well-formed before you
assemble the rest of the run.

## From the command line

Point `julesconf validate` at the file rather than at the directory:

```bash
julesconf validate run/namelists/jules_soil.nml
```

The file is matched to its schema by name, so the argument must be one of the
29 namelist files julesconf models. Anything else — a namelist julesconf
deliberately does not model, such as `cable_pfts.nml`, or a name it does not
recognise at all — is a usage error and exits `2`.

Validation failures are reported exactly as they are for a whole directory:

```
Validation failed (1 error):

  jules_soil.nml  JULES_SOIL  soilhc_method
    9 is not a valid value; valid values: 1, 2, 3
```

`--strict` works here too, and escalates anything julesconf cannot represent —
an unmodelled member, for instance — to a failure.

## What single-file validation cannot check

Every run prints this, and it is the important part:

```
Checked this file alone. The <cross-namelist> rules were skipped: the list
lengths tied to npft, ncpft, nnvg and ntype, which are declared in
jules_surface_types.nml, and the consistency rules that read switches from more
than one namelist.

This file passing does not mean the configuration is valid. Run julesconf
validate on the namelists directory to run those checks too.
```

Per-file validation checks that file's own bounds, enums, types and any rule
whose inputs all live in the same file. It cannot check:

- list lengths tied to `npft` / `nnvg` / `ncpft` / `ntype`, because those
  dimensions are declared in `jules_surface_types.nml`;
- rules spanning two namelists, such as the single-pool soil carbon model being
  incompatible with TRIFFID.

Those live on [`JulesNamelists`](../api/schemas/namelists.md) and need the whole
directory:

```bash
julesconf validate run/namelists
```

The notice is printed even under `--quiet`, which drops advisory output but not
statements about what was left unchecked.

## From Python

The same check, for programmatic use:

```python
from julesconf.schemas import JulesNamelists

block = JulesNamelists.from_namelist_file("run/namelists/jules_soil.nml")
```

It returns the validated model — the same object a whole-directory read leaves
on `JulesNamelists.jules_soil` — and raises `pydantic.ValidationError` if the
file is invalid. The same caveats apply: no cross-namelist rule runs.

If you already have the data in hand, you can validate a block against its model
directly. Every namelist module exposes a top-level model named after the file
(`TimestepsNamelist` for `timesteps.nml`, and so on) — see the
[schemas overview](../api/schemas/index.md) for the full list:

```python
from julesconf.config import NamelistFileHandler
from julesconf.schemas.timesteps import TimestepsNamelist

data = NamelistFileHandler().read("run/namelists/timesteps.nml")
TimestepsNamelist.model_validate(data)
```

For the length checks, validate the whole directory instead:

```python
from julesconf.schemas import JulesNamelists

JulesNamelists.from_namelists("run/namelists")
```
