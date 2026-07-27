"""Gate the rule disposition lockfile against the committed rose metadata extract.

`tests/data/rose_meta/vn7.9.json` holds every conditional (`fail-if` /
`trigger` / `warn-if`) rule the JULES vn7.9 rose metadata declares.
`tests/data/rose_meta/rules_disposition.toml` records what julesconf does about
each one. This module keeps the two in step:

- every rule in the extract has a disposition entry;
- every disposition entry names a rule that still exists;
- the expression hash recorded in the disposition still matches the extract, so
  an edit to the extract cannot slip past unnoticed;
- every `implemented` entry's `where` resolves to something that exists.

`status = "todo"` deliberately does *not* fail. The lockfile is a tracked
backlog; the gate is that every upstream rule has been looked at.

Everything here is hermetic: no network, no JULES checkout.
"""

import hashlib
import json
import re
import tomllib
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "rose_meta"
EXTRACT = DATA / "vn7.9.json"
DISPOSITION = DATA / "rules_disposition.toml"

STATUSES = frozenset({"implemented", "covered-by-listlen", "out-of-scope", "todo"})
"""The status vocabulary, documented in the lockfile's header comment."""


@pytest.fixture(scope="module")
def rules() -> dict[str, dict]:
    """Every rule in the committed extract, keyed by rule id."""
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    return {
        rule["id"]: rule
        for entry in extract["fields"].values()
        for rule in entry.get("rules", ())
    }


@pytest.fixture(scope="module")
def disposition() -> dict[str, dict]:
    """The committed disposition lockfile."""
    return tomllib.loads(DISPOSITION.read_text(encoding="utf-8"))


def test_every_rule_has_a_disposition(rules, disposition):
    """A rule the extract knows about must have been looked at."""
    missing = sorted(set(rules) - set(disposition))
    assert not missing, (
        f"{len(missing)} rule(s) have no disposition entry; run"
        " `python scripts/rose_meta_extract.py disposition`. First few:"
        f" {missing[:5]}"
    )


def test_no_disposition_entry_has_rotted(rules, disposition):
    """A disposition entry for a rule that no longer exists is stale."""
    extra = sorted(set(disposition) - set(rules))
    assert not extra, (
        f"{len(extra)} disposition entr(ies) name a rule absent from the"
        f" extract. First few: {extra[:5]}"
    )


def expression_hash(expression: str) -> str:
    """Recompute a rule's digest from its expression.

    Deliberately an independent reimplementation of
    `scripts/rose_meta_extract.py::rule_hash`. Comparing the two *stored*
    hashes would only catch a regenerated extract; recomputing catches a
    hand-edited one too, where the expression moved and the `hash` field was
    left behind.
    """
    return hashlib.sha256(" ".join(expression.split()).encode()).hexdigest()[:16]


def test_extract_hashes_match_their_expressions(rules):
    """The extract's own hashes must describe the expressions it ships."""
    tampered = sorted(
        rule_id
        for rule_id, rule in rules.items()
        if rule["hash"] != expression_hash(rule["expression"])
    )
    assert not tampered, (
        f"{len(tampered)} rule(s) in the extract carry a hash that does not"
        f" match their expression. First few: {tampered[:5]}"
    )


def test_hashes_match_the_extract(rules, disposition):
    """A silently-edited rule expression must not keep its old disposition.

    The hash covers the normalised expression only, so rewording an upstream
    `#` comment does not trip this, while changing what the rule *tests* does.
    """
    drifted = sorted(
        rule_id
        for rule_id, entry in disposition.items()
        if rule_id in rules
        and entry.get("hash") != expression_hash(rules[rule_id]["expression"])
    )
    assert not drifted, (
        f"{len(drifted)} rule expression(s) changed since their disposition was"
        f" recorded; re-read them and update the lockfile. First few:"
        f" {drifted[:5]}"
    )


def test_every_status_is_in_the_vocabulary(disposition):
    """Keep the status vocabulary small and documented."""
    unknown = sorted(
        {
            entry.get("status", "<missing>")
            for entry in disposition.values()
            if entry.get("status") not in STATUSES
        }
    )
    assert not unknown, f"unknown status(es): {unknown}"


def test_implemented_entries_name_a_validator(disposition):
    """Every `implemented` entry's `where` must resolve to a real attribute.

    Guards against a validator being renamed or deleted while the lockfile
    still claims the rule is enforced.
    """
    import importlib

    unresolved = []
    for rule_id, entry in sorted(disposition.items()):
        if entry.get("status") != "implemented":
            continue
        where = entry.get("where")
        if where is None:
            unresolved.append(f"{rule_id}: no `where`")
            continue
        module_name, _, path = where.partition(".")
        try:
            obj = importlib.import_module(f"julesconf.schemas.{module_name}")
            for part in path.split("."):
                obj = getattr(obj, part)
        except (ImportError, AttributeError):
            unresolved.append(f"{rule_id}: {where}")
    assert not unresolved, "unresolved `where` targets:\n  " + "\n  ".join(unresolved)


def test_covered_by_listlen_entries_name_a_dimension(disposition):
    """A `covered-by-listlen` entry must name a dimension the machinery knows."""
    from julesconf.schemas.constraints import LIST_LEN_DIMS, SIBLING_DIMS

    known = set(LIST_LEN_DIMS) | set(SIBLING_DIMS)
    bad = [
        f"{rule_id}: {entry.get('where')}"
        for rule_id, entry in sorted(disposition.items())
        if entry.get("status") == "covered-by-listlen"
        and not any(f"'{dim}'" in str(entry.get("where")) for dim in known)
    ]
    assert not bad, "unknown ListLen dimension(s):\n  " + "\n  ".join(bad)


def test_out_of_scope_entries_are_postponed_namelists(rules, disposition):
    """`out-of-scope` is reserved for the namelists julesconf excludes by policy."""
    import re

    from julesconf.schemas import POSTPONED_NAMELISTS

    def postponed(block: str) -> bool:
        return (
            block in POSTPONED_NAMELISTS
            or block == "jules_red"
            or block.startswith("cable_")
        )

    pattern = re.compile(r"^namelist:(?P<block>[^=]+)=")
    bad = [
        rule_id
        for rule_id, entry in sorted(disposition.items())
        if entry.get("status") == "out-of-scope"
        and rule_id in rules
        and not postponed((pattern.match(rule_id) or {"block": ""})["block"])
    ]
    assert not bad, f"`out-of-scope` used outside a postponed namelist: {bad[:5]}"


def test_todo_entries_carry_a_reason(disposition):
    """A backlog entry is only useful if it says why it is on the backlog."""
    silent = [
        rule_id
        for rule_id, entry in sorted(disposition.items())
        if entry.get("status") == "todo" and not entry.get("reason")
    ]
    assert not silent, f"`todo` entries with no reason: {silent[:5]}"


def test_no_todo_reason_names_something_julesconf_now_models():
    """A `todo` reason of "does not model X" must still be true of X.

    The gap this closes is the one that let 47 rules sit in the backlog with a
    blocker that had stopped existing: a later phase modelled the member, and
    nothing re-read the dispositions. Every other gate here checks that a rule
    *has* a disposition, not that its stated reason still holds, so the file
    rots in the one direction that hides available work rather than surfacing
    it.

    `jules_soil_ecosse` is the legitimate case and stays: it is a deliberate
    scope exclusion, not a gap (see `AGENTS.md`).
    """
    from julesconf.schemas import JulesNamelists

    disposition = tomllib.loads(DISPOSITION.read_text())

    def modelled(name: str) -> bool:
        """Whether `block` or `block=member` resolves against the schemas."""
        block, _, member = name.partition("=")
        for field in JulesNamelists.model_fields.values():
            annotation = field.annotation
            sub = getattr(annotation, "model_fields", None)
            if sub is None or block not in sub:
                continue
            if not member:
                return True
            inner = sub[block].annotation
            return member in (getattr(inner, "model_fields", None) or {})
        return False

    stale = []
    for rule_id, entry in sorted(disposition.items()):
        if entry.get("status") != "todo":
            continue
        match = re.search(r"does not model ([\w=]+)", entry.get("reason", ""))
        if match and modelled(match.group(1)):
            stale.append(f"{rule_id}: claims {match.group(1)} is not modelled")
    assert not stale, (
        "`todo` reasons that are no longer true — the member is modelled now,"
        " so the rule is implementable:\n  " + "\n  ".join(stale)
    )
