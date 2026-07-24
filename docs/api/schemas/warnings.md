# Warnings and errors

julesconf prefers to **warn and continue** rather than fail, so that a config from
another JULES version, or one using an out-of-scope namelist, still reads. Each
situation has its own class, so you can escalate them independently — see
[enforce strict validation](../../how-to/strict-validation.md) for how.

## Warnings

### `UnknownNamelistKeyWarning`

A member *within* a namelist julesconf models that it does not recognise — usually
a typo (which JULES itself silently ignores) or a parameter from a different
version. The member is ignored. On a path headed for `to_namelists` this means
silent data loss, so escalate it with `strict=True` when the config will be
re-emitted.

::: julesconf.schemas.UnknownNamelistKeyWarning

### `PostponedNamelistWarning`

A whole namelist that is [deliberately out of scope](../../concepts/coverage.md) —
`cable_*`, `oasis_rivers` or `red_params`. The file is not modelled; the warning
exists so the exclusion is visible rather than looking like support.

::: julesconf.schemas.PostponedNamelistWarning

### `ToleratedLengthWarning`

Emitted when writing the [grouped TOML form](grouped.md) from a config whose TRIFFID
array was supplied at the tolerated `npft` length rather than `nnpft`. The trailing
unread values have nowhere to go in the grouped form and are truncated (lossless
for the model run, lossy for the bytes). The warning names the field and both
lengths, and points to `to_toml(..., grouped=False)` as the escape hatch.

::: julesconf.schemas.ToleratedLengthWarning

## Errors

### `GroupedConfigError`

Raised when a grouped config is internally inconsistent in a way validation cannot
paper over — most often a **partial specification**: a parameter set by some
`[[pft]]` entries but not others, which a Fortran namelist array cannot express.
The message names the offending entry and field.

::: julesconf.schemas.GroupedConfigError

## Escalating warnings to errors

All four use the standard `warnings` machinery, so each can be turned into an error
on its own:

```python
import warnings
from julesconf.schemas import PostponedNamelistWarning

warnings.simplefilter("error", PostponedNamelistWarning)
```

For the common case — unknown members on a config you intend to re-emit — prefer
the `strict=True` argument to `from_namelists` / `from_toml`.
