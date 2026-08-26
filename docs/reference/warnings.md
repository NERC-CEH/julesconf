# Warnings and errors

julesconf prefers to **warn and continue** rather than fail, so that a config from another JULES version, or one using an out-of-scope namelist, still reads.
Each situation has its own class, so you can escalate them independently — see [enforce strict validation](../guide/namelists.md#members-julesconf-does-not-model) for how.

## Warnings

### `UnknownNamelistKeyWarning`

A member *within* a namelist julesconf models that it does not recognise — usually a typo (which JULES itself silently ignores) or a parameter from a different version.
The member is ignored.
On a path headed for `to_namelists` this means silent data loss, so escalate it with `strict=True` when the config will be re-emitted.

::: julesconf.schemas.UnknownNamelistKeyWarning

### `PostponedNamelistWarning`

A whole namelist that is [deliberately out of scope](coverage.md) — `cable_*`, `oasis_rivers` or `red_params`.
The file is not modelled; the warning exists so the exclusion is visible rather than looking like support.

::: julesconf.schemas.PostponedNamelistWarning

### `RepeatedNamelistGroupWarning`

A namelist group that appeared more than once in one file, where julesconf models a single block of it.
All but the first are dropped, so re-emitting the config loses them.

The three groups JULES itself repeats — `jules_output_profile`, `jules_prescribed_dataset` and `jules_deposition_species` — are modelled as **lists of blocks**, one entry per occurrence, and do not raise this.
In TOML they are arrays of tables (`[[output.jules_output_profile]]`), and each block is validated against its own `nvars`.
So this warning now means something narrower: a group julesconf does not know can repeat, most likely one a JULES version newer than v7.9 made repeatable.

::: julesconf.schemas.RepeatedNamelistGroupWarning

### `InactiveNamelistKeyWarning`

A member that holds a non-default value JULES will never read, because a switch elsewhere in the config selects a different scheme, or a repeated group beyond the number the config asks JULES to read — `kaps` under the 4-pool soil carbon model, the RFM river parameters under TRIP, the bedrock parameters with `l_bedrock = FALSE`.
These come from the `trigger` rules in the JULES rose metadata, which rose greys out in its config editor and JULES simply ignores.
Not an error, but rarely what the author intended.

Only a value that *differs from the schema default* is reported, so a config that has been through `to_namelists` — which writes every member julesconf holds a default for — does not warn about every inactive member of every unused scheme.

::: julesconf.schemas.InactiveNamelistKeyWarning

### `DiscouragedValueWarning`

A value JULES accepts and acts on, but which its own authors advise against: a deprecated option, a scheme tuned only for some other setting, or a value with a physical consequence that is rarely intended.
These come from the `warn-if` rules in the JULES rose metadata, and the message is the JULES developers' own wording.

This is the one warning here that does **not** mean anything was dropped, ignored or truncated — the setting takes effect exactly as written.
Everything else on this page reports a limitation of how julesconf handles your config; this one reports a scientific opinion about the config itself.
A project with a considered reason to disagree can filter this category alone and keep the rest.

::: julesconf.schemas.DiscouragedValueWarning

### `ToleratedLengthWarning`

Emitted when writing the [grouped TOML form](api/grouped.md) from a config whose TRIFFID array was supplied at the tolerated `npft` length rather than `nnpft`.
The trailing unread values have nowhere to go in the grouped form and are truncated (lossless for the model run, lossy for the bytes).
The warning names the field and both lengths, and points to `to_toml(..., grouped=False)` as the escape hatch.

::: julesconf.schemas.ToleratedLengthWarning

## Errors

### `GroupedConfigError`

Raised when a grouped config is internally inconsistent in a way validation cannot paper over — most often a **partial specification**: a parameter set by some `[[pft]]` entries but not others, which a Fortran namelist array cannot express.
The message names the offending entry and field.

::: julesconf.schemas.GroupedConfigError

## Escalating warnings to errors

All of these use the standard `warnings` machinery, so each can be turned into an error on its own:

```python
import warnings
from julesconf.schemas import PostponedNamelistWarning

warnings.simplefilter("error", PostponedNamelistWarning)
```

For the common case — unknown members on a config you intend to re-emit — prefer the `strict=True` argument to `from_namelists` / `from_toml`.
