---
icon: lucide/rocket
---

# Getting started

## Install

=== "uv"

    ```sh
    uv add julesconf
    ```

=== "pip"

    ```sh
    pip install julesconf
    ```

    Then add `julesconf` to your `pyproject.toml` by hand.

julesconf needs Python 3.12 or newer.
Installing also puts a `julesconf` command on your path:

```sh
julesconf --version
julesconf validate run/namelists
```

## The one object

Everything in the library goes through `JulesNamelists`, the validated configuration model.
It reads and writes both file forms, and the four methods are peers — any read pairs with any write:

| | Namelists | TOML |
|---|---|---|
| **Read** | `from_namelists(dir)` | `from_toml(path)` |
| **Write** | `to_namelists(dir)` | `to_toml(path)` |

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")
config.to_namelists("run/namelists")
```

Reading validates as it goes, so a bad config fails at the read rather than at the JULES run.
Every command in the [CLI](../reference/cli.md) is a thin shell over one or two of these calls.

## Which page do you want

| You have | You want | Go to |
|---|---|---|
| A directory of `.nml` files | To check it, edit it, and write it back | [Working with namelists](namelists.md) |
| Nothing yet, or a config to start from | To author a config as one readable file | [Working with TOML](toml.md) |
| A `rose-app.conf` | Namelists or TOML, without a rose installation | [Coming from rose](rose.md) |
| Namelists plus driving data and initial conditions | To read or move the data files too | [Data files](data-files.md) |
| A parameter to sweep | Many configs, built in Python | [Generating configs](generating-configs.md) |

If you would rather read code than prose, the [worked example](worked-example.md) runs the Loobos flux-tower configuration end to end.
