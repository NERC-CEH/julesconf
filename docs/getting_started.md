# Getting Started

## Installing `julesconf`

### As a project dependency

Install and add to your `pyproject.toml`:

=== "uv"

    ```sh
    uv add julesconf
    ```

=== "pip"

    ```sh
    pip install julesconf
    ```

    Then manually add `julesconf` to `pyproject.toml`.

julesconf requires **Python 3.12 or newer**.

Installing also puts a `julesconf` command on your path:

```
julesconf --version
julesconf validate run/namelists
```

See the [command-line reference](api/cli.md).

### As a stand-alone CLI tool (TODO)

Not yet implemented.

## Work with a existing namelist-based config

TODO

## Generate namelists from a TOML config

TODO

...

## Old

This tutorial gets you from a JULES config to a validated model and back, in both [file forms](../concepts/file-forms.md).

### The one object you need

Everything here goes through `JulesNamelists`, the validated configuration model:

```python
from julesconf.schemas import JulesNamelists
```

It has four methods — a reader and a writer for each format:

| | Namelists | TOML |
|---|---|---|
| **Read** | `from_namelists(dir)` | `from_toml(path)` |
| **Write** | `to_namelists(dir)` | `to_toml(path)` |

### Read a config

Reading validates as it goes — bounds, enums, and the cross-namelist consistency checks — so a bad config fails here.

=== "From namelists"

    ```python
    config = JulesNamelists.from_namelists("run/namelists")
    ```

=== "From TOML"

    ```python
    config = JulesNamelists.from_toml("config.toml")
    ```

Either way you now hold the same validated `JulesNamelists`.

### Edit a parameter

```python
config.timesteps.jules_time.timestep_len = 3600  # an hourly timestep
```

An out-of-range value raises a `ValidationError` (try `timestep_len = 0`).

### Write it out

Write to whichever format you need.

=== "To namelists"

    ```python
    config.to_namelists("run/namelists-new")
    ```

=== "To TOML"

    ```python
    config.to_toml("config.toml")
    ```

The written namelists contain every parameter, including those left to their default value.
This is intentional: JULES does not (at the time of writing) reliably default to the parameter values described in the documentation (I think these defaults are actually Rose defaults..?).

## Next steps

...

