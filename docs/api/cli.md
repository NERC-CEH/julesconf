---
icon: lucide/terminal
---

# Command line

Installing julesconf puts a `julesconf` command on your path. It is a thin
shell over [`JulesNamelists`](schemas/namelists.md) and `julesconf.rose` — every
command maps onto one or two library calls — so that validating a configuration
or converting between the file forms needs no Python.

```bash
julesconf --version
julesconf --help
```

## Commands

| Command | What it does |
|---|---|
| `julesconf validate <target>` | Validate a namelists directory or a `.toml` config |
| `julesconf convert rose2nml <conf> -o <dir>` | Convert a `rose-app.conf` to namelist files |
| `julesconf convert rose2toml <conf> -o <file>` | Convert a `rose-app.conf` to a TOML config |
| `julesconf convert toml2nml <file> -o <dir>` | Write the namelists a TOML config describes |
| `julesconf convert nml2toml <dir> -o <file>` | Read namelists and write them as TOML |

### `validate`

```bash
julesconf validate run/namelists
julesconf validate config.toml --strict
```

The argument may be a directory of `.nml` files or a `.toml` config in either
form; which one it is is detected from the path. `--strict` escalates
julesconf's warnings to errors, exactly as `strict=True` does on
`from_namelists` / `from_toml` — see
[enforce strict validation](../how-to/strict-validation.md).

### `convert rose2nml` and `convert rose2toml`

```bash
julesconf convert rose2nml  rose-app.conf -o namelists/
julesconf convert rose2toml rose-app.conf -o config.toml
```

Both accept `--on-unbound keep|error|empty`, which decides what happens to an
environment variable the app references but nothing binds. `keep` is the
default. See [convert a rose app to TOML](../how-to/rose-to-toml.md) for why
this matters in practice.

### `convert toml2nml` and `convert nml2toml`

```bash
julesconf convert toml2nml config.toml -o run/namelists
julesconf convert nml2toml run/namelists -o config.toml
```

The namelists written by `convert toml2nml` will be larger than the ones you started
from: every member julesconf holds a default for is stated explicitly, so the
files fully determine the run. See
[the explicit-defaults guarantee](../concepts/defaults-guarantee.md).

## Common options

| Option | Applies to | Meaning |
|---|---|---|
| `--strict` | `validate`, `rose2toml`, `toml2nml`, `nml2toml` | Treat julesconf's warnings as errors |
| `--flat` | `rose2toml`, `nml2toml` | Write the flat TOML form instead of the grouped `[[pft]]` form |
| `--on-unbound` | `rose2nml`, `rose2toml` | `keep` (default), `error` or `empty` |
| `--overwrite` | every command that writes | Replace existing output; without it, an existing output is an error |
| `--quiet`, `-q` | every command | Drop advisory output. Data-loss warnings and errors are still shown |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | The configuration is invalid, or the conversion failed |
| `2` | The command line itself was wrong — a missing argument, an unknown option, a path that does not exist |

Nothing else is ever returned, so the tool can be scripted:

```bash
julesconf validate run/namelists --strict --quiet || exit 1
```

## Validation failures

A raw pydantic error names a member by its position in the model tree. The CLI
renders it the way JULES writes it instead — file, namelist group, member:

```
Validation failed (3 errors):

  jules_soil.nml  JULES_SOIL  dzsoil_io
    dzsoil_io has 3 element(s), expected sm_levels=4

  jules_soil_biogeochem.nml  JULES_SOIL_BIOGEOCHEM  soil_bgc_model
    'roth_c' is not a valid name; valid names: ['single_pool', 'four_pool',
      'ecosse']

  jules_vegetation.nml  JULES_VEGETATION  can_rad_mod
    7 is not a valid value; valid values: 1, 2, 3, 4, 5, 6
```

An error raised by a rule spanning the whole config — for instance the
single-pool soil carbon model under TRIFFID — has no single home, and is shown
as `<cross-namelist>`.

The formatter lives in `julesconf._errors` and does not depend on the CLI, so
library code can produce the same report:

```python
from pydantic import ValidationError
from julesconf._errors import format_validation_error
from julesconf.schemas import JulesNamelists

try:
    JulesNamelists.from_namelists("run/namelists")
except ValidationError as exc:
    print(format_validation_error(exc))
```

## Warnings

Warnings are collected, grouped by category and sorted by consequence rather
than printed one line at a time in arrival order:

```
9 warnings:

  UnknownNamelistKeyWarning (4) -- data loss
    These members are not in julesconf's schemas and are ignored, so writing
    the config back out drops them.
    - JulesSurface: ignoring unknown namelist member 'l_vary_z0m_soil'
      ...
```

Each category carries a **severity band**:

- **data loss** — part of the configuration cannot be represented and is being
  dropped, so writing it back out would lose it.
  `RepeatedNamelistGroupWarning`, `UnknownNamelistKeyWarning` and
  `PostponedNamelistWarning` are all in this band, and
  `RepeatedNamelistGroupWarning` is listed first because it is a modelling gap
  rather than something you can fix in your config. It is rare: the groups
  JULES actually repeats — output profiles, prescribed datasets, deposition
  species — are modelled as lists of blocks and do not warn.
- **advisory** — the configuration is representable, but something in it is
  probably not doing what its author intended.
  `InactiveNamelistKeyWarning` sets a member JULES will not read given the
  switches elsewhere in the config.

`--quiet` suppresses the advisory band and the success line; the data-loss band
is always shown. `--strict` turns julesconf's warnings into a failure. The
[warnings and errors](schemas/warnings.md) reference describes each class in
full.

## Colour

Output is colourised only when it is going to a terminal. Piped to a file or
captured in CI it is plain text, wrapped at a fixed width so the layout does
not depend on the terminal it was produced on.
