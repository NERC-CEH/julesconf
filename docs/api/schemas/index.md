# Schemas

Pydantic validation schemas for JULES namelist files, pinned to the
[JULES v7.9 user guide](https://jules-lsm.github.io/user_guide/doc/source/namelists/).
Each page corresponds to one `.nml` file and documents the namelist blocks and
 their parameters.

The top-level `JulesNamelists` model (documented below)
combines all 29 namelist files and performs cross-namelist consistency checks
(e.g. list lengths against `npft` / `nnvg`).

## Usage

```python
from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists, JULES_VERSION

data = NamelistConfig().read("/path/to/jules/namelists")
m = JulesNamelists.model_validate(data)
```

## Behaviour notes

- **Unknown keys:** every model emits a `UnknownNamelistKeyWarning` when it
  encounters a namelist member it does not recognise. This surfaces typos
  (which JULES itself silently ignores) without rejecting configs that contain
  members the schema does not yet cover. To escalate warnings to hard errors::

      import warnings
      from julesconf.schemas import UnknownNamelistKeyWarning

      warnings.simplefilter("error", UnknownNamelistKeyWarning)

- **Sentinel values:** many real-valued fields accept `-1.0` as a JULES sentinel
  meaning "use the default".

## Top-level model

::: julesconf.schemas.namelists.JulesNamelists
