---
icon: lucide/refresh-cw
---

# Staying in sync with JULES

julesconf's schemas are a hand-maintained transcription of a specification that lives in someone else's repository and changes without notice.
Keeping them honest is most of the maintenance work, so it is automated as far as it can be and made loud where it cannot.

## The three upstream sources

| Source | What it is | How julesconf uses it |
|---|---|---|
| `docs/source/namelists/*.rst` in [jules-lsm.github.io](https://github.com/jules-lsm/jules-lsm.github.io) | The user guide: prose, units, `:type:` and `:permitted:` | Documented ground truth for field types, bounds and defaults |
| `rose-meta/jules-standalone/vn7.9/` plus its ten `jules-shared` imports in [MetOffice/jules](https://github.com/MetOffice/jules) | A machine-readable spec: types, ranges, enums, array dimensions, and the `fail-if` / `trigger` / `warn-if` rules | Extracted to `tests/data/rose_meta/vn7.9.json`; what the coverage audit compares against |
| `rose-stem/app/*/rose-app.conf` in MetOffice/jules | Around 57 real, tested configurations | Conformance corpus — ten vendored in `tests/data/rose_apps/`, the rest swept when a checkout is available |

The metadata is split across eleven files: the standalone `rose-meta.conf` opens with an `import=` naming ten `jules-shared` packages, and the specification is the standalone file plus all ten.
Merging happens per *setting*, not per section — some fields are described in a shared package and then given extra `trigger` or `fail-if` settings by the standalone file.
The import list is read from the file rather than hardcoded.

## When two sources disagree

They do, regularly: the user guide and the rose metadata state different bounds, a rule is malformed, an enum is missing a value that live configs still use.

There is no blanket rule for which wins.
Decide on the evidence for that specific field, and record the reasoning where the next person will find it — the schema docstring for a modelling decision, the disposition file for a rule.
Do not silently follow one source because it was easier to read.

## The extract, and why it is committed

```sh
python scripts/rose_meta_extract.py extract \
    --jules-repo reference/jules --version vn7.9 -o tests/data/rose_meta/vn7.9.json
```

`reference/` is gitignored, so a checkout of MetOffice/jules is optional for contributors.
The normalised JSON extract is committed instead, which means the audit and the drift check need neither the clone nor the network.

Work from the committed extract, not from raw `rose-meta` files.

The script has four subcommands:

| Subcommand | What it does |
|---|---|
| `extract` | Reads a local JULES checkout and writes the normalised JSON extract with a provenance header |
| `audit` | Walks `JulesNamelists` against a committed extract and prints a coverage report |
| `disposition` | Refreshes `tests/data/rose_meta/rules_disposition.toml` |
| `drift` | Diffs a fresh extract against the committed one and renders the changes as Markdown |

## The rules disposition lockfile

Every conditional rule in the extract — each `fail-if`, `trigger` and `warn-if` — gets one entry in `tests/data/rose_meta/rules_disposition.toml`, recording what julesconf does about it:

| Status | Meaning |
|---|---|
| `implemented` | julesconf enforces the rule; `where` names the validator |
| `covered-by-listlen` | A `len(this) != <dim>` rule enforced generically by the `ListLen` machinery; `where` names the annotation |
| `out-of-scope` | The rule belongs to a namelist julesconf deliberately does not model |
| `todo` | Looked at, not implemented; `reason` says why |

`hash` is a digest of the rule's normalised expression, so an upstream edit that is not reflected here fails `tests/schemas/test_rose_rule_coverage.py`.

The gate is only that every upstream rule *appears* in the file.
`todo` is a legitimate answer and does not fail the test — the thing being prevented is a rule changing under julesconf without anyone noticing, not a rule going unimplemented.

Regenerating preserves the `status`, `where` and `reason` of every entry whose rule still exists, refreshes hashes, adds new rules with an auto-assigned status, and drops entries whose rule has gone.
So the workflow after upstream moves is: regenerate, then curate the new entries by hand.

## The monthly drift check

`.github/workflows/rose-meta-freshness.yml` runs at 05:17 on the 1st of each month, and on demand.
It takes one sparse clone of MetOffice/jules and does two things with it.

1. Rebuilds the extract from upstream `main` and diffs it against the committed one, annotating each added, removed or changed rule with its disposition.
2. Runs `tests/rose/test_sweep.py`, which converts and validates every `rose-stem/app/*/rose-app.conf` — the wide version of the ten vendored apps the offline suite covers.

Both report into the **same** issue as separately titled sections, under the `rose-meta-drift` label.
They are two symptoms of one cause, and triaging them together is what a maintainer actually wants; splitting them would mean two issues arriving on the same morning about the same commit.

It opens an issue rather than a pull request on purpose.
The right response to a new `fail-if`, or to an app that stopped validating, is a judgement call — implement it, defer it, or rule it out of scope — not a mergeable diff.

## Running the wide sweep locally

The sweep skips itself unless the checkout is present:

```sh
git clone --filter=blob:none --sparse \
    https://github.com/MetOffice/jules reference/jules
git -C reference/jules sparse-checkout set rose-meta rose-stem
pytest tests/rose/test_sweep.py
```

Nothing is hardcoded about which apps exist, so a newer upstream commit that adds or removes apps changes the tally rather than breaking the test.

## Do not depend on rose

`metomi-rose` is GPL-3 and julesconf is MIT, so it is not a dependency and cannot become one.
The rose format parser in `julesconf.rose` is hand-written for that reason.
