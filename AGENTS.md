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
- CLI is a thin shell: no validation/path logic in `cli.py`. `markup=False` on rich output.
- `warn_inactive` compares value to schema default, not `model_fields_set`.
- Tests: must `chdir` into `tmp_path`. Loobos has no crops/TRIFFID — use synthetic fixtures for those.
- Docs: `zensical` (mkdocs-material), NOT sphinx — no `:class:`, `.. note::`, double-backtick, etc.
