---
icon: lucide/play
---

# Get started

This tutorial gets you from a JULES config to a validated model and back, in both
[file forms](../concepts/file-forms.md). The two are peers — read whichever you
have, write whichever you want.

If you have not installed julesconf yet, see [install](../how-to/install.md).

## The one object you need

Everything here goes through `JulesNamelists`, the validated configuration model:

```python
from julesconf.schemas import JulesNamelists
```

It has four methods — a reader and a writer for each format:

| | Namelists | TOML |
|---|---|---|
| **Read** | `from_namelists(dir)` | `from_toml(path)` |
| **Write** | `to_namelists(dir)` | `to_toml(path)` |

## Read a config

Point a reader at what you have. Reading validates as it goes — bounds, enums, and
the cross-namelist consistency checks — so a bad config fails here.

=== "From namelists"

    ```python
    config = JulesNamelists.from_namelists("run/namelists")
    ```

=== "From TOML"

    ```python
    config = JulesNamelists.from_toml("config.toml")
    ```

Either way you now hold the same validated `JulesNamelists`.

## Edit a parameter

The model is typed, so you reach parameters by attribute, and edits are
re-validated:

```python
config.timesteps.jules_time.timestep_len = 3600  # an hourly timestep
```

An out-of-range value raises a `ValidationError` naming the field — try
`timestep_len = 0` to see it.

## Write it out

Write to whichever format you need. JULES consumes namelists; TOML is the readable
form to keep under version control.

=== "To namelists"

    ```python
    config.to_namelists("run/namelists-new")
    ```

=== "To TOML"

    ```python
    config.to_toml("config.toml")
    ```

The written namelists are deliberately **more explicit** than what you read: every
parameter julesconf holds a default for is stated, so the files fully determine the
run. See [the explicit-defaults guarantee](../concepts/defaults-guarantee.md).

## Where next

You have seen the core loop: **read → edit → write**, in either format. From here:

- **[Authoring a config in TOML](authoring-toml.md)** — build a config in the terse
  grouped form, the recommended path for new projects.
- **[Editing namelists directly](editing-namelists.md)** — work at the raw
  directory layer, including input data (driving data, initial conditions, tile
  fractions).
- **[The two file forms](../concepts/file-forms.md)** and
  **[the containers](../concepts/containers.md)** — the concepts behind all of the
  above.
