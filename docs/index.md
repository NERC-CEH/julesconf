---
icon: lucide/rocket
---

# julesconf

More robust tooling for JULES configurations. A JULES run is configured through 29
Fortran namelist files; julesconf gives you a validated model over them, and a
single readable TOML file you can configure a run from instead.

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")   # or from_namelists(dir)
config.to_namelists("run/namelists")               # write what JULES consumes
```

Or from a shell, with no Python at all:

```bash
julesconf convert rose2toml rose-app.conf -o config.toml
julesconf convert toml2nml  config.toml   -o run/namelists
```

Namelists stay first-class — read and write them directly. TOML is the terse form
recommended for new projects, with a
[grouped form](api/schemas/grouped.md) that turns each surface type into one named
table so a length mismatch is not even expressible.
[Why does this help?](concepts/why-not-namelists.md)

## Find your way

- **[Tutorials](tutorials/get-started.md)** — learn by doing. Start with
  **[Get started](tutorials/get-started.md)**, then
  **[author a config in TOML](tutorials/authoring-toml.md)** or
  **[edit namelists directly](tutorials/editing-namelists.md)**.
- **[How-to guides](how-to/install.md)** — task recipes:
  [install](how-to/install.md),
  [migrate a legacy config](how-to/migrate-to-toml.md),
  [convert a rose app](how-to/rose-to-toml.md),
  [add a PFT](how-to/add-a-pft.md),
  [enforce strict validation](how-to/strict-validation.md).
- **[Concepts](concepts/why-not-namelists.md)** — how it fits together:
  [the two file forms](concepts/file-forms.md),
  [the containers](concepts/containers.md),
  [the defaults guarantee](concepts/defaults-guarantee.md),
  [what julesconf covers](concepts/coverage.md).
- **[Reference](api/schemas/namelists.md)** —
  the [command line](api/cli.md),
  [`JulesNamelists`](api/schemas/namelists.md),
  [option values](api/schemas/enums.md),
  [warnings and errors](api/schemas/warnings.md),
  and the [per-namelist schemas](api/schemas/index.md).
