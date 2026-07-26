---
icon: lucide/download
---

# Install julesconf

julesconf requires **Python 3.12 or newer**.

## Add it to a project

julesconf is developed with [uv](https://docs.astral.sh/uv/). To add it as a
dependency of your own project:

```
uv add julesconf
```

Or with pip:

```
pip install julesconf
```

## Verify the install

```python
from julesconf.schemas import JulesNamelists, JULES_VERSION

print(JULES_VERSION)   # the JULES user-guide version the schemas are pinned to
```

`JULES_VERSION` tells you which JULES release the schemas track — see
[what julesconf covers](../concepts/coverage.md) for why that matters.

Installing also puts a `julesconf` command on your path:

```
julesconf --version
julesconf validate run/namelists
```

See the [command-line reference](../api/cli.md).

## Set up for development

To work on julesconf itself, clone the repository and sync the full environment,
including the dev and docs dependency groups:

```
uv sync --group dev --locked
just
```

`just` (with no argument) runs lint, typecheck, tests and a docs build. Always
pass `--locked` for a reproducible install. See `AGENTS.md` in the repository for
the full set of tasks.

## Next steps

- New to julesconf? Work through [Get started](../tutorials/get-started.md).
- Have an existing namelists run? See
  [migrate a legacy config to TOML](migrate-to-toml.md).
- Working from a rose suite? See
  [convert a rose app to TOML](rose-to-toml.md).
