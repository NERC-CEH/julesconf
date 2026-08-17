# julesconf

`julesconf` brings robust Python tooling to support working with configurations of the [JULES](https://github.com/MetOffice/jules) land surface model.
It is useful when manually editing Fortran namelists and hoping for the best is not enough, but the full machinery provided by Rose and Cylc is too much.

`julesconf` provides:

1. A Python dataclass-like interface to a JULES configuration comprising namelists and data files with read/write, based on [dirconf]() and [f90nml]().
  E.g. **INSERT CODE**
  This is particularly useful for generating ensembles by systematically varying namelist parameters.

2. Validation using a Pydantic model / schema, which is constructed from the official [JULES documentation]() (but actually enforces the stated defaults)
  E.g. **INSERT CODE**

3. An alternative config format: a single TOML file, which can be easier to work with.

E.g.

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")   # or from_namelists(dir)
config.to_namelists("run/namelists")               # write what JULES consumes
```

For a deeper dive into each of these features, see **INSERT PAGES**.

## Philosophy

- Any check that can be automated, ideally should be. The cost of failing to validate is too high. Look before you leap for an expensive complex model is essential.
- Can't fix things within JULES itself - have to operate in the outer layer
- Prefer to rely on standard tools with large user bases and financial backing (Python, pydantic)

## See also

- dirconf
- portable-jules
