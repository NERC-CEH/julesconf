---
icon: lucide/layers
---

# Generating configs

Perturbed-parameter ensembles, sensitivity sweeps and anything else that needs many nearly-identical runs are the case julesconf is most useful for.
The pattern is always the same: read one config, copy it per run, change what varies, validate, write.

## Start from a template, not from nothing

`JulesNamelists` has required fields with no defaults — `drive`, `initial_conditions`, `timesteps` and others — so there is no useful empty config to build up from.
Read a working configuration and treat it as the template:

```python
from julesconf.schemas import JulesNamelists

template = JulesNamelists.from_toml("examples/loobos/loobos.toml")
```

Reading once and copying is also the fast path.
Validation is the expensive part, and this way you pay for the template's read once rather than per member of the ensemble.

## Copy deeply

```python
run = template.model_copy(deep=True)
```

`deep=True` matters.
A shallow `model_copy()` shares the nested namelist blocks with the template, so the first run's edit changes the template and every run after it inherits the change.

## Sweep

```python
import itertools
from pathlib import Path

out = Path("ensemble")

for timestep, zsmc in itertools.product([1800, 3600], [0.5, 1.0]):
    run = template.model_copy(deep=True)
    run.timesteps.jules_time.timestep_len = timestep
    run.jules_soil.jules_soil.zsmc = zsmc

    JulesNamelists.model_validate(run.to_namelist_dict())
    run.to_namelists(out / f"ts{timestep}-zsmc{zsmc}" / "namelists")
```

That writes four run directories of 29 complete namelist files each.

The `model_validate` line is not decoration.
Attribute assignment is unchecked, so without it a value out of bounds, or a combination of switches JULES rejects, reaches the run directory intact and fails hours later inside JULES.
`to_namelist_dict()` returns what `to_namelists` is about to write, so validating it checks the thing that will actually be on disk, including the cross-namelist rules.

## Vary a surface type

Per-surface-type parameters are parallel lists on the flat model, indexed by surface type:

```python
run.pft_params.jules_pftparm.canht_ft_io = [19.01, 16.38, 0.79, 1.26, 1.0]
```

If a sweep varies the *number* of surface types rather than their parameters, work through the grouped TOML form instead — `npft`, the index members and every array length are derived from the entries, so adding one is one table rather than a coordinated edit across five files.
See [add a surface type](toml.md#add-a-surface-type).

## Leave the data where it is

Namelists change per ensemble member; driving data and initial conditions almost never do.
Write only the namelists per run and point all of them at one shared data directory, rather than copying gigabytes per member.

The paths JULES resolves are the ones in the namelists, so an absolute path to a shared directory, or a relative path that resolves the same way from every run directory, is all this takes.
[Data files](data-files.md) covers the container layer if you do need to move the data as well.

## Feeding a containerised JULES

Nothing above needs JULES installed, so the natural split is to generate and validate configs on the host and mount them into the container:

```sh
docker run --rm \
  -v "$PWD/ensemble/ts1800-zsmc0.5/namelists:/run/namelists:ro" \
  -v "$PWD/data:/run/data:ro" \
  jules:7.9
```

Validating before the container starts is the point.
A config error caught by `model_validate` costs a second; the same error caught by JULES costs a scheduler slot and whatever the queue wait was.

For a shell-driven pipeline the CLI does the same job without a Python process:

```sh
julesconf validate ensemble/ts1800-zsmc0.5/namelists --strict --quiet || exit 1
```

Exit codes are `0` for success, `1` for an invalid config, and `2` for a bad command line, and nothing else is ever returned — see the [command-line reference](../reference/cli.md).
