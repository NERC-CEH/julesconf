# julesconf

```
uv sync --group dev --locked && just
```

## Gotchas

- Two upstream sources (RST docs + rose metadata) can contradict. No blanket rule — decide on evidence, record in `notes/UPSTREAM.md`. `reference/` is gitignored; use the committed extract (`tests/data/rose_meta/vn7.9.json`), not raw rose-meta.
- `jules_soil_ecosse`, `cable_*`, `oasis_rivers`, `red_params` are deliberately NOT modelled (scope decisions). Don't add schemas. `jules_deposition_species_specific` IS a backlog gap (safe to add).
- Repeated groups: no scalar-or-list coercion for blocks. Too many blocks is legal (surplus = `InactiveNamelistKeyWarning`). Sibling dims per-element. Fields inside repeated groups can't pivot to grouped TOML.
- `ListLen` must sit on the outermost `Annotated`. Wrong spelling is silently invisible to `FieldInfo.metadata`.
- Don't depend on `metomi-rose` — GPL-3, julesconf is MIT. Rose format parser is hand-written.
- Don't propose replacing the pydantic schemas with a generated JSON Schema per JULES version. Settled: `rose-meta` has no `default=` key anywhere, so defaults exist only in the upgrade macros and a generated schema can't produce a complete config. JSON Schema also can't do sibling dims, derived defaults, cross-namelist validators or the three warning severities. The single-version pin is caused by import-time global state, not by pydantic.
- CLI is a thin shell: no validation/path logic in `cli.py`. `markup=False` on rich output.
- `warn_inactive` compares value to schema default, not `model_fields_set`.
- Tests: must `chdir` into `tmp_path`. Loobos has no crops/TRIFFID — use synthetic fixtures for those.
- Docs: `zensical` (mkdocs-material), NOT sphinx — no `:class:`, `.. note::`, double-backtick, etc.

## `notes/`

Design and decision records. **Gitignored** — local to the maintainer's checkout, so never
cite them from shipped code, docs or commit messages; quote the reasoning inline instead.
Layout: `plans/done/` is design reasoning for work that shipped, `logs/` is what happened.
Every file carries a status banner; trust that over anything below.

**Outstanding work is not tracked in this repo.** As of 2026-08-25 it lives in GitHub issues
and in the maintainer's own notes, so do not look for a to-do list here and do not add one.
`TODO.md` and the unbuilt `plans/` tree are gone; what is left is the record of decisions
already taken. Issue #5 is the live one: multi-version support, JULES v8+ only.

Top level:

- `UPSTREAM.md` — JULES upstream defects: RST-vs-metadata contradictions, malformed rules, enums missing values still in use. Add to it whenever the two sources disagree.

`plans/done/` — designs whose work has shipped, kept for the reasoning:

- `plans/done/toml_config.md` — why TOML, the defaults policy, and the grouped `[[pft]]` form. Explains `PerElementDefault` and the all-or-none rule better than the code does.
- `plans/done/rose_converter.md` — pre-implementation design for rose→namelist. Still authoritative on the rose *file format* (§2) and on why rose ships no such converter itself (§1).
- `plans/done/rose_meta.md` — what the `rose-meta` tree contains and how the conditional-validation half was built. Track A (the version-upgrade generator) was never built and moved out; the stub that replaces it keeps the three findings worth not re-deriving.
- `plans/done/enum_migration.md` — the `int` → `IntEnum` conversion, fully implemented. Kept for the member-naming rationale and the `model_dump(mode="json")` serialization note.
- `plans/done/roadmap.md` — the old work register; retains the CLI error-format sketch the formatter was built to.
- `plans/done/docs_reorg.md` — the Diátaxis restructure of `docs/`, fully implemented. Consult §4 for where a new page belongs.

`logs/` — records of work carried out:

- `logs/rose_implementation_log.md` — the rose integration, phase by phase, with findings and plan deviations; also holds the PR-message draft. The record of what was actually built and why.
- `logs/schema_gap_inventory.md` — triage of the 290 vn7.9 members julesconf once lacked. The gap is now zero; keep it for the add/defer/out-of-scope reasoning.
- `logs/none_defaults_inventory.md` — the 459 fields defaulting to `None`, triaged into those that could take a real default and the 38 that must not.
- `logs/alpha_prep_log.md` — what closing the enum, conditional-validation, CLI and schema-fix items involved, and the decisions taken.
