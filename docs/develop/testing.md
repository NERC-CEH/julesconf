---
icon: lucide/flask-conical
---

# Tests and release

## Running the suite

```sh
uv sync --group dev --locked && just
```

`just` with no argument runs `lint`, `typecheck` and `test`.
Individually:

| Recipe | What it runs |
|---|---|
| `just lint` | `ruff format`, `ruff check --fix`, and `marimo check examples/` |
| `just lint-check` | The same without modifying files, as CI runs it |
| `just typecheck` | `pyright` |
| `just test` | `pytest` |
| `just test-cov` | `pytest` with coverage, failing under 90% |
| `just docs` | Re-exports the worked example from `examples/101.py`, then `zensical build` |

CI runs lint and typecheck once, and the suite on Python 3.12, 3.13 and 3.14.

## Test layout

| Path | Covers |
|---|---|
| `tests/schemas/` | Bounds, constraints, enums, conditional rules, cross-namelist checks, rose rule coverage |
| `tests/rose/` | The rose config parser, the app model, conversion, the metadata extract, and the upstream sweep |
| `tests/test_config.py` | The directory containers and file handlers |
| `tests/test_toml.py`, `tests/test_toml_grouped.py` | Both TOML forms and the grouped pivot |
| `tests/test_cli.py` | The command line, including exit codes and output format |
| `tests/test_integration_loobos.py` | The Loobos configuration end to end |
| `tests/test_docs_coverage.py` | That the enum and warning reference pages list every class that exists |

Two things to know before writing a test.

**Tests must `chdir` into `tmp_path`.** The directory containers require relative paths, so a test that writes anywhere else will not behave the way library code does.

**Loobos has no crops and no TRIFFID.** For `ncpft > 0` or TRIFFID coverage, use a synthetic fixture or one of the vendored rose apps rather than adapting the Loobos config.

## The anti-drift tests

Several tests exist only to fail when the code and something outside it diverge.
They assert set equality in both directions, so a stale entry is caught as loudly as a missing one.

- `test_docs_coverage.py` — the enum and warning reference pages are hand-written lists of `:::` directives, so nothing otherwise stops a new class from being added and never appearing in the docs. That is how the enums page came to be missing 13 of 45 enums while still building and still looking complete.
- `test_grouped_models.py::test_generated_model_covers_exactly_its_dims` — the grouped `Pft` / `CropPft` / `Nvg` models are generated from `ListLen` metadata, so this asserts the generated fields match the dimensions exactly.
- `test_cross_namelist.py::test_every_list_len_uses_canonical_spelling` — `ListLen` is invisible to Pydantic if it is not on the outermost `Annotated`, and the failure is silent. See [adding a schema](adding-a-schema.md).
- `test_rose_rule_coverage.py` — every conditional rule upstream has a disposition entry whose hash still matches. See [staying in sync with JULES](upstream.md).

If you find yourself weakening one of these, that is the signal to check whether the drift it caught is real.

## Release

`.github/workflows/publish.yml` holds a three-mode publishing workflow — a tag push to TestPyPI, a GitHub Release to PyPI, and a manual run choosing either — but the whole thing is currently commented out.
Releases are not yet wired up; uncommenting it is the remaining step.
