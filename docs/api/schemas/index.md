# Schemas

Pydantic validation schemas for JULES namelist files.
Each page corresponds to one `.nml` file and documents the namelist blocks and
their parameters, mirroring the
[JULES v7.9 user guide](https://jules-lsm.github.io/user_guide/doc/source/namelists/).

The top-level `JulesNamelists` model (documented below)
combines all 29 namelist files and performs cross-namelist consistency checks
(e.g. list lengths against `npft` / `nnvg`).

## Usage

```python
from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists

data = NamelistConfig().read("/path/to/jules/namelists")
m = JulesNamelists.model_validate(data)
```

## Top-level model

::: julesconf.schemas.namelists.JulesNamelists
