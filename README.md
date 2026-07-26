# julesconf

More robust tooling for JULES configurations. Configure a JULES run from a
single readable TOML file, and let julesconf write the 29 Fortran namelist
files the model consumes — filling in every parameter it holds a default for,
so the written config determines the run.

```python
from julesconf.schemas import JulesNamelists

config = JulesNamelists.from_toml("config.toml")
config.to_namelists("/path/to/jules/namelists")
```

The TOML [grouped form](https://nerc-ceh.github.io/julesconf/api/schemas/grouped.html)
pivots the parallel per-surface-type arrays — spread across `pft_params.nml`,
`triffid_params.nml`, `jules_snow.nml` and `crop_params.nml` — into named
`[[pft]]` / `[[crop_pft]]` / `[[nvg]]` tables, so each surface type is one
object and a length mismatch is not even expressible.

There is a command-line interface too, so a validation check needs no Python:

```
julesconf validate run/namelists --strict
julesconf rose2toml rose-app.conf -o config.toml
```

It exits `0` on success, `1` on an invalid config and `2` on a usage error, and
reports each failure as `file.nml  NAMELIST_BLOCK  member` rather than as a
pydantic traceback.

See the [documentation](https://nerc-ceh.github.io/julesconf) for the
configuration guide, the grouped form, the command line, and the full API
reference.

## Quick start

```
uv sync --group dev --locked
just
```
