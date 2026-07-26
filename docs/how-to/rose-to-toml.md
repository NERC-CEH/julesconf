---
icon: lucide/import
---

# Convert a rose app to TOML

Inside the Met Office suite ecosystem a JULES configuration is a
`rose-app.conf`: one INI-style file whose `[file:…]` sections describe the
namelist files to stage and whose `[namelist:…]` sections hold their contents.
julesconf reads them, so you can turn one into a validated
[TOML config](../concepts/file-forms.md) without a rose installation.

Conversion is one-way. julesconf reads rose apps; it never writes them.

## The one-liner

```bash
julesconf rose2toml rose-app.conf -o config.toml
```

That does three things: converts the app to namelist text exactly as rose's own
namelist location handler would, validates the result against julesconf's
schemas, and writes it back out in the grouped `[[pft]]` form.

Add `--flat` for the [flat form](../concepts/file-forms.md) that mirrors the
namelists one-to-one.

If you only want the namelist files — for a run directory, or to diff against
an existing one — stop at the first step:

```bash
julesconf rose2nml rose-app.conf -o namelists/
```

## Expect unresolved environment variables

A rose app is **not self-contained**. Values routinely reference variables the
cylc workflow supplies rather than the app itself:

```
[namelist:jules_drive]
file='$LOOBOS_INSTALL_DIR/Loobos_1997.dat'
```

Converting offline, there is no workflow to supply `$LOOBOS_INSTALL_DIR`, so
the CLI names every variable it could not resolve:

```
Unresolved environment variables (3):
  $DUMP_FILE
  $LOOBOS_INSTALL_DIR
  $ROSE_TASK_NAME
```

By default (`--on-unbound keep`) the reference is written into the output
verbatim, which is honest but means any path containing one is a path that does
not exist. Three ways to deal with it:

=== "Bind them"

    ```bash
    LOOBOS_INSTALL_DIR=/data/loobos \
    DUMP_FILE=/data/dumps/loobos.dump \
    ROSE_TASK_NAME=loobos \
    julesconf rose2toml rose-app.conf -o config.toml
    ```

=== "Blank them"

    ```bash
    julesconf rose2toml rose-app.conf -o config.toml --on-unbound empty
    ```

=== "Refuse to guess"

    ```bash
    julesconf rose2toml rose-app.conf -o config.toml --on-unbound error
    ```

    This is what rose itself does: an unbound variable is a hard failure.

## Read the warnings

A real rose app usually converts with warnings, grouped by category and
labelled with whether they are advisory or mean something is dropped. Two are
worth knowing about up front.

**Repeated namelist groups.** JULES lets a namelist group appear more than once
in one file — `jules_output_profile` occurs once per output profile,
`jules_prescribed_dataset` once per prescribed dataset,
`jules_deposition_species` once per species. julesconf models each as a list of
blocks, so every occurrence is converted and written back out. In TOML they are
arrays of tables:

```toml
[[output.jules_output_profile]]
profile_name = "daily"
nvars = 2
var = ["gpp", "smcl"]

[[output.jules_output_profile]]
profile_name = "monthly"
nvars = 1
var = ["gpp"]
```

Each profile carries its own `nvars`, and each is validated against it. The
count member — `nprofiles` here — has to match: fewer groups than it asks for
is an error, and more is allowed but reported, since JULES reads the leading
`nprofiles` and ignores the rest. Rose apps often carry spare profiles that
way.

A group julesconf models a *single* block of that nonetheless appears twice
still warns (`RepeatedNamelistGroupWarning`) — that one really is dropped; see
[what julesconf covers](../concepts/coverage.md).

**Postponed namelists.** Rose apps describe the `cable_*`, `oasis_rivers` and
`red_params` namelists too. julesconf deliberately does not model them; they
are neither validated nor written.

To make either of these a hard failure instead, add `--strict`.

## From Python

The CLI is a thin shell over the library, so the same conversion is three
calls:

```python
from julesconf.rose import rose_app_to_namelists
from julesconf.schemas import JulesNamelists

files = rose_app_to_namelists("rose-app.conf", "namelists/")
print(sorted(files.unresolved))  # the variables nothing bound

JulesNamelists.from_namelists("namelists/").to_toml("config.toml")
```

`rose_app_to_namelists` returns the `{filename: text}` mapping it wrote, with
`.substituted` and `.unresolved` attached, so the environment report travels
with the result rather than needing a second pass.

## Then check it

```bash
julesconf validate config.toml
```

See the [command-line reference](../api/cli.md) for the full command surface
and the exit codes.
