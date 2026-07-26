# JULES rose app corpus

Six real `rose-app.conf` files, vendored verbatim from the JULES model's
`rose-stem` test suite. They exist so the rose → namelist converter is tested
against configurations julesconf did not write, and so the schemas get a
conformance corpus that reaches parts of JULES the rest of the test suite does
not.

## Provenance

- Upstream: [MetOffice/jules](https://github.com/MetOffice/jules),
  `rose-stem/app/<name>/rose-app.conf`.
- Commit: `aa0f60ff68a62e0ab9b9a8c538ddaa404c1d859b` (2026-07-22).
- Vendored: 2026-07-26.
- Each file is copied byte for byte; only the name changes, from
  `<name>/rose-app.conf` to `<name>.conf`.

## Why these six

| `loobos_crops` | crop PFTs — `ncpft > 0`, the documented blind spot in the rest of the suite |
|---|---|
| `loobos_trif` | TRIFFID dynamic vegetation, likewise unexercised by the Loobos example |
| `gswp2_gl7` | gridded rather than single-site: `tpl_name`, file-driven ancillaries |
| `loobos_jules_es_1p0_deposition` | indexed `namelist:jules_deposition_species(N)` sections |
| `loobos_fire` | the fire module |
| `loobos_irrig` | irrigation, including `jules_irrig_props` |

Every one of them declares `meta=jules-standalone/vn8.2` while julesconf's
schemas are pinned to vn7.9, so they also serve as a rolling record of the
version gap — see `tests/rose/test_convert.py::TestCorpus`.

## Refreshing

```
git clone --filter=blob:none --sparse https://github.com/MetOffice/jules reference/jules
git -C reference/jules sparse-checkout set rose-meta rose-stem
cp reference/jules/rose-stem/app/<name>/rose-app.conf tests/data/rose_apps/<name>.conf
```

`reference/` is gitignored; the checkout is not part of this repository. The
apps are committed so the test suite needs neither the checkout nor the network.

## Licence and attribution

These files are © Crown copyright, Met Office, and are distributed by the JULES
project under the **BSD 3-Clause Licence**. julesconf is MIT licensed, which is
compatible: the BSD-3-Clause terms continue to apply to these vendored files,
and the copyright notice, conditions and disclaimer are preserved in the
upstream repository's `LICENCE` file.
