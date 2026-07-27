# julesconf

Python configuration management for the JULES land surface model.

## Quick start

```
uv sync --group dev --locked
just
```

## Commands

| `just` (default) | lint + typecheck + test + docs |
|---|---|
| `just lint` | `ruff format && ruff check --fix` |
| `just lint-check` | `ruff format --check && ruff check` (CI-safe, no writes) |
| `just test` | `pytest` |
| `just test-cov` | `pytest --cov=julesconf --cov-report=term-missing --cov-fail-under=90` |
| `just typecheck` | `pyright` |
| `just docs` | `zensical build` |

## Key locations

| `src/julesconf/cli.py` | The `julesconf` console script (typer). A thin shell over `JulesNamelists` + `julesconf.rose` — no logic of its own |
|---|---|
| `src/julesconf/_errors.py` | Maps pydantic error `loc`s to `file.nml / BLOCK / member` and groups warnings by severity band. No CLI dependency; usable from library code |
| `src/julesconf/config.py` | DirConfig classes (NamelistConfig, InputFilesConfig, JulesConfig) + 3 file handlers |
| `src/julesconf/schemas/` | Pydantic v2 models for 29 JULES namelists (pinned to v7.9) |
| `src/julesconf/schemas/_namelists.py` | Top-level `JulesNamelists` combining all 29 + cross-namelist checks |
| `src/julesconf/schemas/constraints.py` | Public field vocabulary: `Fraction`, `NonNegFloat`, `ZeroOne`, `SentinelOrFraction`, `ListLen`, `name_or_value` |
| `src/julesconf/rose/_config.py` | `RoseConfig` — parser/serialiser for the Met Office rose INI format. Pure format layer, knows nothing about JULES |
| `src/julesconf/schemas/_grouped.py` | Grouped TOML form: generated `Pft`/`CropPft`/`Nvg` models + `assemble`/`disassemble` |
| `tests/test_config.py` | Handler + DirConfig tests (hypothesis property-based) |
| `tests/test_cli.py` | CLI + error-formatter tests. The formatter is tested directly **and** through the CLI |
| `tests/rose/test_config.py` | Rose format tests. Fixtures are hand-written miniatures — the real `rose-app.conf`/`rose-meta.conf` files are deliberately **not** vendored |
| `src/julesconf/schemas/_conditional.py` | `InactiveNamelistKeyWarning` + the `is_specified` / `warn_inactive` / `fail_if` helpers the rose `fail-if` / `trigger` validators are built from |
| `tests/data/rose_meta/rules_disposition.toml` | Disposition lockfile: one entry per rose rule, gated by `tests/schemas/test_rose_rule_coverage.py` |
| `tests/schemas/` | Schema tests grouped by concern (`test_bounds`, `test_enums`, `test_cross_namelist`, `test_constraints`, `test_extra_keys`, `test_namelists`, `test_grouped_models`) |
| `tests/test_toml_grouped.py` | Phase 2 gates. The **only** cover for crop PFTs — Loobos has `ncpft = 0` |
| `examples/loobos/` | Real Loobos config (29 `.nml` files + input data). Used by `examples/101.py`, **not** by the test suite |
| `scripts/rose_meta_extract.py` | Dev CLI: `extract` normalises the upstream JULES rose metadata into JSON, `audit` compares it against the schemas |
| `tests/data/rose_apps/` | Ten real `rose-app.conf` files vendored from JULES `rose-stem` (BSD-3-Clause). The conformance corpus behind `tests/rose/test_convert.py::TestCorpus`; 93% of the `(block, member)` pairs the full upstream suite sets |
| `tests/rose/test_sweep.py` | The wide sweep: every upstream app, **skipped** without the `reference/jules` checkout. `KNOWN_UNKNOWN_MEMBERS` and the corpus stay the offline gate |
| `tests/data/rose_meta/vn7.9.json` | The committed extract (BSD-3-Clause, see the README beside it). Regenerate with `extract`; the test suite and audit never need `reference/jules` |

## Reference docs (ground truth)

`reference/jules-lsm.github.io/user_guide/doc/source/namelists/` — official JULES v7.9 RST docs for every namelist. This is the authoritative source for schema field definitions, types, and bounds. `reference/.../input/` documents the ASCII/NetCDF input data format.

`reference/jules/rose-meta/` — the machine-readable spec shipped with the model (a sparse clone of MetOffice/jules; `reference/` is gitignored, never commit it). `jules-standalone/vn7.9/rose-meta.conf` is **not** the whole spec: it opens with an `import=` list of ten `jules-shared/*/vn7.9` packages, and blocks such as `jules_nvegparm` live only in the shared tree. Merging is per *setting*, not per section, imports first. `scripts/rose_meta_extract.py` does all of this; use the committed extract rather than re-parsing.

**When the two sources contradict each other, there is no blanket rule — decide on evidence and record it in `UPSTREAM.md`.** The tiebreaker is what the shipped `rose-stem` configurations actually do, since those are tested against the model itself. In practice the metadata has won every time so far (`cfrac_s_io` dimension, `yr_fch4_ref` type, `tmax_io` spelling), but not always: `JULES_RIVERS_PROPS::is_climatology` is documented only in the user guide and is missing from the metadata entirely. Note also that a namelist is not always documented in the RST file its name suggests — `JULES_RIVERS_PROPS` lives in `ancillaries.nml.rst`, and assuming otherwise has already produced one wrong conclusion.

`UPSTREAM.md` (committed, repo root) is the running list of these discrepancies, cited by section number from the schema docstrings that depend on them. Add to it rather than burying the reasoning in `notes/`, which is gitignored.

### Postponed namelists

`cable_*`, `oasis_rivers` and `red_params` have reference docs but **deliberately have no schemas**. They configure rarely-used JULES extensions (the CABLE land surface scheme, OASIS river coupling, and the RED vegetation demography model) that would add substantial modelling complexity for very few users. This is a scoping decision, not a gap to be filled — do not add schemas for them without discussing it first.

Consequences to be aware of:

- Coverage figures must be computed over the 29 schema'd namelists only. Counting members across all `*.nml.rst` includes the postponed ones and overstates the gap.
- A config using these namelists is out of scope, and julesconf says so rather than appearing to support it: `PostponedNamelistWarning` is emitted when one is detected, both on reading a namelists directory and on validating a config dict (`_namelists.py`).
- `POSTPONED_NAMELISTS` names namelist *files*; the rose metadata is keyed by *block*, and the two do not correspond (`red_params` is block `jules_red`, `cable_pfts` is `cable_pftparm`). `scripts/rose_meta_extract.py` keeps its own `POSTPONED_META_BLOCKS` for this reason.

### Repeated namelist groups

Fortran lets one namelist group appear several times in a file, and JULES relies on it: `jules_output_profile` occurs `JULES_OUTPUT::nprofiles` times, `jules_prescribed_dataset` occurs `JULES_PRESCRIBED::n_datasets` times, and `jules_deposition_species` occurs `JULES_DEPOSITION::ndry_dep_species` times. **These three are modelled as lists of blocks** — `list[JulesOutputProfile]` and friends — one entry per occurrence, in file order. `REPEATABLE_GROUPS` (`schemas/_namelists.py`) is derived from the annotations, so declaring a new one is a one-line change.

- **The one-vs-many ambiguity is resolved at the handler boundary**, in `config.namelist_to_dict`. `f90nml` gives a bare `Namelist` for one occurrence, a `Cogroup` for several, and `_grp_<group>_<n>` keys once `todict()` flattens either; `read` returns a `list[dict]` of length ≥ 1 for a repeatable group, and `write` emits one Fortran group per entry via `add_cogroup`. An empty list writes no group.
- **Do not add scalar-or-list coercion for blocks.** `_base._coerce_scalars_to_lists` exists for the different reason that Fortran writes a one-element array indistinguishably from a scalar, and explicitly excludes repeated-group fields. A TOML config must write `[[output.jules_output_profile]]` even for one profile. One strict internal shape.
- **All three list fields default to empty**, matching their count members' default of zero/unset. `to_namelist_dict` therefore writes no group at all for a config with no profiles, where it used to write one empty block.
- **Four walks descend per element**, carrying a 1-based index in the path: `_base.iter_leaf_fields` (class walk — no index, so it marks the path element with `REPEATED_GROUP_MARK`), `_namelists._expand_per_element_defaults`, `_namelists.JulesNamelists._check_model_list_lengths`, and `tests/conftest.py::walk_fields`. `walk_fields` **stays independently written** — see its docstring.
- **Sibling dimensions are per element.** Each profile's `var`/`output_type`/`var_name` is checked against *that* profile's `nvars`, and `PerElementDefault` expands to that profile's length.
- **Count consistency** lives on the file-level model (`OutputNamelist`, …), the smallest model that can see both the count and the blocks, via `_conditional.check_group_count`. Too few blocks raises; **too many is legal** — JULES reads the leading `count` and ignores the rest, and real rose apps ship spare profiles (`loobos_jules_es_1p0_deposition`: 7 profiles, `nprofiles = 2`) — so a surplus block that sets something raises `InactiveNamelistKeyWarning`, and an empty placeholder block is silent. Rose has no `fail-if` for this; it expresses repetition as `duplicate=true`, so these checks are julesconf's own.
- **A field inside a repeated group cannot be pivoted into the grouped TOML form.** `_grouped._build_specs` skips them: `JULES_DEPOSITION_SPECIES::rsurf_std_io` is `ListLen("ntype")` but there is one such array *per species*, so no `[[pft]]` entry can hold a single value for it. `ntype` consequently contributes no fields to the grouped form today, and `rsurf_std` is no longer on `Pft`/`Nvg`.
- `RepeatedNamelistGroupWarning` survives with a **narrower meaning**: a group julesconf models as a *single* block that turned up repeated anyway — a group made repeatable after v7.9, or a hand-built dict still carrying `_grp_` keys. `namelist_to_dict` deliberately preserves the `_grp_` mangling for those rather than picking one silently. `strict=True` still escalates it.
- `tests/schemas/test_repeated_groups.py` is the dedicated cover, and `tests/rose/test_convert.py::REPEATED_GROUPS` pins the per-app counts. **`jules_deposition_species` repeats nowhere in the corpus** — the deposition app's species sections are `!!`-ignored — so it and its `rsurf_std_io` annotation are covered synthetically.

## Architecture

- `NamelistFileHandler` converts `f90nml` OrderedDict → plain dict via json round-trip, and normalises repeated groups into lists (`namelist_to_dict`; see "Repeated namelist groups")
- `AsciiFileHandler` / `NetcdfFileHandler` use `@dirconf.filter` + `@dirconf.filter_missing` — require relative paths, handle missing files gracefully; `__module__` is patched manually after the decorator (dirconf bug)
- Handlers registered via `register_handler("ascii", ...)` / `register_handler("netcdf", ...)` for extension-based dispatch
- `NamelistModel` base uses `extra="ignore"` + `_warn_unknown_keys` — unknown keys produce `UnknownNamelistKeyWarning`, not errors (escalate with `warnings.simplefilter("error", ...)`). Three warning classes coexist and are escalated independently: `UnknownNamelistKeyWarning` (unknown *member*), `PostponedNamelistWarning` (known-but-unsupported *file*), `RepeatedNamelistGroupWarning` (a group julesconf holds one of that occurs more than once)
- `ListLen` metadata on fields enables cross-namelist dimension validation in `JulesNamelists._check_list_lengths`, which walks the whole model tree via `find_list_len`
- `ListLen` must sit on the **outermost** `Annotated`: `Annotated[list[X] | None, ListLen("npft")]`. The other spelling hides it from `FieldInfo.metadata`; `test_cross_namelist.py::test_every_list_len_uses_canonical_spelling` enforces this
- Enum fields accept int value OR string name via `name_or_value()` validator
- Conditional rules come from the JULES rose metadata and split by severity: `fail-if` → `ValueError` via `@model_validator(mode="after")`; `trigger` → `InactiveNamelistKeyWarning`, because JULES *ignores* an inactive member rather than rejecting it. Cross-namelist rules live on `JulesNamelists`; block-local ones live in their own module
- `warn_inactive` fires only when a member **differs from its schema default**, not on `model_fields_set`. `to_namelist_dict` writes every defaulted member, so a read-write-read cycle would otherwise warn about every inactive member of every unused scheme
- Every rose rule has an entry in `tests/data/rose_meta/rules_disposition.toml` (`implemented` / `covered-by-listlen` / `out-of-scope` / `todo`). `todo` does **not** fail CI — the gate is only that every upstream rule has been looked at. Regenerate with `python scripts/rose_meta_extract.py disposition`, which preserves curated statuses
- Module naming rule: public modules in `schemas/` are named after `.nml` files, one-to-one. Everything else is either `_`-prefixed (`_base.py`, `_namelists.py`) or the shared `constraints.py`, and is re-exported from `schemas/__init__.py`
- Each namelist module's `__all__` lists its top-level `*Namelist` model **and** its per-block models (`JulesPftparm`, …) — both are public
- TOML has two forms. Flat mirrors the namelists one-to-one; grouped pivots the `ListLen` fields into `[[pft]]`/`[[crop_pft]]`/`[[nvg]]` arrays of tables. `to_toml` writes **grouped by default**; `from_toml` auto-detects. `grouped=False` is the escape hatch, and is required to preserve a TRIFFID array supplied at the tolerated `npft` length
- `Pft`/`CropPft`/`Nvg` are **generated** from `ListLen` metadata via `create_model`, never hand-written. `test_grouped_models.py::test_generated_model_covers_exactly_its_dims` is the anti-drift guard that makes this safe; it deliberately uses a second, independent model walk (`tests/conftest.py::walk_fields`) so a bug in `_base.iter_leaf_fields` cannot hide from it
- `CONTRIBUTORS` in `_grouped.py` is the single source of truth for both group membership and array ordering (natural PFTs, then crop PFTs, then non-vegetated)
- `julesconf.rose` is written from scratch against the format, **not** on top of `metomi-rose` — that package is GPL-3 and julesconf is MIT. Do not add it as a dependency
- `RoseConfig.dump` exists so that `parse -> dump` byte-identity is available as the parser's acceptance test; julesconf does not ship rose configs. It writes in declaration order rather than sorting (rose sorts on write, so files rose produced come back unchanged either way)
- `NamelistModel` sets `use_attribute_docstrings=True`, so the `"""…"""` under each field becomes its `FieldInfo.description` and carries into the generated models and the API docs

## Testing quirks

- Tests **must `chdir` into tmp_path** because handlers filter absolute paths
- Hypothesis + `tmp_path` fixtures need `suppress_health_check=[HealthCheck.function_scoped_fixture]`
- Tests build their own synthetic namelist dicts (`minimal_valid()` / `minimal_grouped()` in `tests/conftest.py`) rather than reading `examples/loobos/`. Commit `4e0678d` decoupled them deliberately; `tests/test_integration_loobos.py` is the single sanctioned exception
- **Loobos does not exercise crops or TRIFFID.** `crop_params.nml` and `triffid_params.nml` are empty and `ncpft` is unset, so `nnpft == npft`. Anything touching `[[crop_pft]]`, `nnpft` ordering or `ListLen.tolerates` needs a synthetic fixture — the integration test will pass regardless

## The CLI

`julesconf` is a console script (`[project.scripts]` → `julesconf.cli:app`), built on `typer`. It must stay a **thin shell**: every command is one or two calls into `JulesNamelists` / `julesconf.rose`, with no validation, conversion or path logic of its own. Anything a command needs that the library cannot do belongs in the library.

- Exit codes are part of the contract and are tested: `0` success, `1` invalid config or failed conversion, `2` usage error (typer/click raises these itself — do not catch them).
- Rendering lives in `_errors.py`, not `cli.py`, so the same reports are available to library callers. It emits plain text wrapped at `_errors.WIDTH`; `cli.py` prints it through `rich` with `markup=False, highlight=False, soft_wrap=True`. Markup **must** stay off — error messages contain literal `[...]` (enum name lists) that rich would otherwise swallow.
- Warnings are grouped by category and carry a severity band from `_errors.WARNING_KINDS`. `RepeatedNamelistGroupWarning` is pinned to the top of the report (`WarningKind.priority`) because it is a modelling gap, not a user error. Adding a warning class to the schemas means adding it to `WARNING_KINDS`; `tests/test_cli.py::test_every_julesconf_warning_has_presentation_metadata` fails otherwise.
- `--quiet` drops the advisory band and the success line only. Data-loss warnings and errors are never suppressed.
- `rose2nml` / `rose2toml` always report unresolved `$VAR` references by name. Under the default `--on-unbound keep` these reach the output verbatim and then fail validation as a bad path, so the report is what stops that looking like a mystery.

## Toolchain quirks

- `uv` (not pip/poetry) — always use `--locked` for reproducible installs
- Python 3.12+ only
- `just` task runner
- `ruff` with Google-style docstrings, line-length 88
- Per-file ruff exemptions: `tests/` → no D rules; `schemas/` → E501 allowed; `examples/*/notebook.py` → B018, E501, F841, RUF001
- `pyright` type-checking venv at `./.venv`
- `uv` config: `exclude-newer = "1 week"`
- Documentation uses `zensical` (mkdocs-material), NOT sphinx — no RST roles (`:class:`, `:meth:`, etc.), no double-backtick syntax, no `.. note::` directives

## CI flow

```
lint job:   lint-check → typecheck
test job:   test-cov across Python 3.12, 3.13, 3.14
docs job:   docs → deploy to GitHub Pages (currently commented out in workflow)
```

`rose-meta-freshness.yml` runs monthly (and on demand): it sparsely clones
`MetOffice/jules` (`rose-meta` **and** `rose-stem`), rebuilds the vn7.9 extract
from upstream `main`, and runs `tests/rose/test_sweep.py` over every upstream
`rose-stem/app`. It opens or updates a single `rose-meta-drift` issue if any
conditional rule moved *or* any app stopped validating — two symptoms of one
cause, triaged together, as separate sections. It never fails the build.
