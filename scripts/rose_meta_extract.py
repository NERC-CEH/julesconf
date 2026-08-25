#!/usr/bin/env python
"""Extract the JULES rose metadata and audit julesconf's schemas against it.

`MetOffice/jules` ships `rose-meta/`, a machine-readable specification of every
JULES namelist member: its type, whether it is compulsory, its array length, its
permitted range or enumeration, and the `fail-if` / `trigger` rules rose applies
to it. julesconf's pydantic schemas are pinned to JULES v7.9, so
`rose-meta/jules-standalone/vn7.9/` is the matching specification.

This script has four subcommands:

- `extract` reads a local checkout of the JULES repository and writes a
  normalised JSON extract of the metadata, with a provenance header. The
  extract is committed to the repository so that the audit, and later drift
  checks, need neither the checkout nor the network.
- `audit` compares a committed extract against a walk of
  `julesconf.schemas.JulesNamelists` and prints a coverage report.
- `disposition` refreshes `tests/data/rose_meta/rules_disposition.toml`, the
  maintainer-owned lockfile recording what julesconf does about each of the
  conditional (`fail-if` / `trigger` / `warn-if`) rules in the extract. Entries
  already in the file are preserved verbatim apart from their `hash`; new rules
  are added with an auto-assigned status, and entries naming a rule that no
  longer exists are dropped.
- `drift` compares a freshly built extract against the committed one and
  renders the added / removed / changed rules as Markdown, annotated with their
  disposition. Driven by `.github/workflows/rose-meta-freshness.yml`.

The metadata is split across eleven files
--------------------------------------------

`jules-standalone/vn7.9/rose-meta.conf` opens with a root-level `import=`
setting naming ten `jules-shared/<package>/vn7.9` packages. The specification is
the standalone file *plus* all ten imports: `jules_nvegparm`, for one, exists
only in the shared tree. The import list is read from the file rather than
hardcoded.

Merging is at the level of individual *settings*, not whole sections: a handful
of fields (`namelist:jules_vegetation=can_rad_mod` among them) are described in
a shared package and then given extra `trigger` or `fail-if` settings by the
standalone file. Imports are applied first, in the order listed, then the
importing file, so the importer wins on conflicts.

Usage:
    python scripts/rose_meta_extract.py extract
    python scripts/rose_meta_extract.py audit
    python scripts/rose_meta_extract.py disposition
    python scripts/rose_meta_extract.py drift upstream.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, get_args

from pydantic.fields import FieldInfo

from julesconf.rose import RoseConfig

UPSTREAM_REPO = "https://github.com/MetOffice/jules"
"""Where the metadata comes from. BSD-3-Clause; see tests/data/rose_meta/README.md."""

DEFAULT_REPO = Path("reference/jules")
"""Default location of the local (gitignored) JULES checkout."""

DEFAULT_VERSION = "vn7.9"
"""JULES release the julesconf schemas are pinned to."""

DEFAULT_EXTRACT = Path("tests/data/rose_meta/vn7.9.json")
"""Where the committed extract lives."""

META_DIR = "rose-meta"
"""Subdirectory of the JULES repository holding the metadata packages."""

STANDALONE = "jules-standalone"
"""Metadata package describing a standalone (non-UM, non-LFRic) JULES run."""

GUI_ONLY_KEYS = frozenset({"ns", "sort-key", "widget[rose-config-edit]"})
"""Settings that only affect the rose config editor's presentation."""

RULE_KEYS = ("fail-if", "warn-if", "trigger")
"""Settings whose value is a `;`-separated list of rules."""

POSTPONED_META_BLOCKS = frozenset({"jules_red"})
"""Metadata blocks for postponed extensions whose names differ from ours.

`julesconf.schemas.POSTPONED_NAMELISTS` names namelist *files* (`red_params`,
`cable_pfts`, …) whereas the metadata names namelist *blocks*. Blocks beginning
`cable_` are excluded by prefix; `jules_red` is the RED demography block, whose
name shares nothing with `red_params`.
"""

_FIELD_SECTION_RE = re.compile(r"^namelist:(?P<block>[^=]+)=(?P<member>.+)$")
_BLOCK_SECTION_RE = re.compile(r"^namelist:(?P<block>[^=]+)$")
_TRIGGER_RE = re.compile(r"^(?P<target>namelist:\w+=\w+|\w+)\s*:\s*(?P<condition>.*)$")
_LEN_RULE_RE = re.compile(
    r"^len\(this\)\s*!=\s*\(?namelist:(?P<block>\w+)=(?P<dim>\w+)\)?$"
)


# --------------------------------------------------------------------------
# Reading and merging the metadata
# --------------------------------------------------------------------------


def collapse_whitespace(text: str) -> str:
    """Collapse every run of whitespace, newlines included, to a single space.

    Continuation lines mean a rule arrives as a multi-line string whose line
    breaks carry no meaning. Collapsing them makes the rule stable against
    reformatting upstream.

    Args:
        text: The text to normalise.

    Returns:
        The text with leading, trailing and repeated whitespace removed.
    """
    return " ".join(text.split())


def rule_hash(expression: str) -> str:
    """Return a short stable digest of a rule expression.

    The digest covers the expression only, with whitespace collapsed, so that
    rewording the trailing `# comment` or reflowing the continuation lines does
    not look like a change of behaviour, while editing the condition does.

    Args:
        expression: The rule expression, comment already removed.

    Returns:
        The first 16 hex characters of the SHA-256 digest.
    """
    normalised = collapse_whitespace(expression)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


def split_rules(section: str, kind: str, value: str) -> list[dict[str, Any]]:
    """Split a `fail-if` / `warn-if` / `trigger` value into individual rules.

    Rules are separated by `;`, and one may carry a `# comment` giving the
    human-readable reason it exists. The comment is written *after* the
    separator, at the end of the physical line, so it arrives at the head of the
    following segment:

        fail-if=this == 1;  # Can't use 1-pool with TRIFFID
               =this == 2;  # Can't use 4-pool without TRIFFID

    A comment reached before any code in a segment therefore explains the
    previous rule; one reached after code on the same line explains its own
    rule, which is how the comment on an unterminated final rule is written.

    A `trigger` rule additionally has the form `<target field>: <condition>`,
    which is split out.

    Args:
        section: Name of the section the setting belongs to, used to build the
            rule ids.
        kind: The setting key, one of `RULE_KEYS`.
        value: The raw setting value, possibly spanning several lines.

    Returns:
        One dict per rule, each with `id`, `kind`, `expression`, `hash` and,
        where present, `reason`, `target` and `condition`.
    """
    rules: list[dict[str, Any]] = []
    for segment in value.split(";"):
        code: list[str] = []
        trailing: list[str] = []
        leading: list[str] = []
        for line in segment.split("\n"):
            source, _, comment = line.partition("#")
            if source.strip():
                code.append(source)
            if comment.strip():
                (trailing if code else leading).append(comment.strip())
        if leading and rules:
            _add_reason(rules[-1], leading)

        expression = collapse_whitespace(" ".join(code))
        if not expression:
            continue
        rule: dict[str, Any] = {
            "id": f"{section}#{kind}#{len(rules) + 1}",
            "kind": kind,
            "expression": expression,
            "hash": rule_hash(expression),
        }
        if trailing:
            _add_reason(rule, trailing)
        if kind == "trigger" and (match := _TRIGGER_RE.match(expression)):
            rule["target"] = match["target"]
            rule["condition"] = match["condition"]
        rules.append(rule)
    return rules


def _add_reason(rule: dict[str, Any], comments: list[str]) -> None:
    """Attach comment text to a rule as its reason.

    Args:
        rule: The rule to annotate.
        comments: Comment fragments, in the order they were written.
    """
    parts = [rule["reason"], *comments] if "reason" in rule else comments
    rule["reason"] = collapse_whitespace(" ".join(parts))


def read_imports(config: RoseConfig) -> list[str]:
    """Return the metadata packages a rose-meta file imports.

    Args:
        config: A parsed `rose-meta.conf`.

    Returns:
        Package paths relative to `rose-meta/`, in the order listed. Empty if
        the file imports nothing.
    """
    setting = config.root.get("import")
    if setting is None:
        return []
    return [line.strip() for line in setting.value.split("\n") if line.strip()]


def load_metadata(
    meta_root: Path, package: str
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Load a metadata package and everything it imports, merged.

    Args:
        meta_root: The `rose-meta/` directory of a JULES checkout.
        package: Package path relative to `meta_root`, e.g.
            `jules-standalone/vn7.9`.

    Returns:
        A `(sections, sources)` pair. `sections` maps section name to its
        settings, with ignored (`!`-prefixed) settings dropped, since rose
        itself does not apply them. `sources` lists the package paths that were
        read, imports first.

    Raises:
        FileNotFoundError: If a package has no `rose-meta.conf`.
    """
    merged: dict[str, dict[str, str]] = {}
    sources: list[str] = []

    def visit(name: str) -> None:
        if name in sources:
            return
        path = meta_root / name / "rose-meta.conf"
        if not path.is_file():
            raise FileNotFoundError(f"no rose-meta.conf for package {name!r}: {path}")
        config = RoseConfig.parse_file(path)
        for imported in read_imports(config):
            visit(imported)
        sources.append(name)
        for section_name, section in config.sections.items():
            settings = merged.setdefault(section_name, {})
            for key, setting in section.settings.items():
                if setting.state:
                    continue
                settings[key] = setting.value

    visit(package)
    return merged, sources


# --------------------------------------------------------------------------
# Normalising into the extract
# --------------------------------------------------------------------------


def split_values(value: str) -> list[str]:
    """Split a `values=` list into its members.

    Members are comma separated and may be Fortran literals, so they are kept
    as raw text rather than coerced.

    Args:
        value: The raw setting value.

    Returns:
        The members, in order, with empty entries dropped.
    """
    return [item for part in value.split(",") if (item := collapse_whitespace(part))]


def parse_range(value: str) -> list[dict[str, float | None]] | None:
    """Parse a `range=` value into numeric segments.

    Rose accepts a comma-separated list of `lo:hi` intervals (either end may be
    omitted, meaning unbounded) and bare values, but also arbitrary expressions
    such as `this>0`, which have no numeric form.

    Args:
        value: The raw setting value.

    Returns:
        One `{"min": …, "max": …}` per segment, using `None` for an open end, or
        `None` if the value is an expression rather than a list of intervals.
    """
    segments: list[dict[str, float | None]] = []
    for part in value.split(","):
        part = collapse_whitespace(part)
        if not part:
            return None
        try:
            if ":" in part:
                low, _, high = part.partition(":")
                segments.append(
                    {
                        "min": float(low) if low else None,
                        "max": float(high) if high else None,
                    }
                )
            else:
                segments.append({"min": float(part), "max": float(part)})
        except ValueError:
            return None
    return segments or None


def normalise_field(section: str, settings: dict[str, str]) -> dict[str, Any]:
    """Normalise one `[namelist:<block>=<member>]` section.

    Args:
        section: The section name.
        settings: Its settings, GUI-only keys included.

    Returns:
        The normalised field entry.
    """
    match = _FIELD_SECTION_RE.match(section)
    assert match is not None
    entry: dict[str, Any] = {"block": match["block"], "member": match["member"]}

    for key in ("type", "length", "description", "help", "title", "url", "pattern"):
        if (value := settings.get(key)) is not None:
            entry[key.replace("-", "_")] = collapse_whitespace(value)

    if (compulsory := settings.get("compulsory")) is not None:
        entry["compulsory"] = compulsory.strip().lower() == "true"
    if (values := settings.get("values")) is not None:
        entry["values"] = split_values(values)
    if (titles := settings.get("value-titles")) is not None:
        entry["value_titles"] = split_values(titles)
    if (bounds := settings.get("range")) is not None:
        entry["range"] = collapse_whitespace(bounds)
        entry["range_segments"] = parse_range(bounds)

    rules = [
        rule
        for key in RULE_KEYS
        if (value := settings.get(key)) is not None
        for rule in split_rules(section, key, value)
    ]
    if rules:
        entry["rules"] = rules

    extra = sorted(set(settings) - GUI_ONLY_KEYS - set(RULE_KEYS) - _KNOWN_FIELD_KEYS)
    if extra:
        entry["other"] = {key: collapse_whitespace(settings[key]) for key in extra}
    return entry


_KNOWN_FIELD_KEYS = frozenset(
    {
        "compulsory",
        "description",
        "help",
        "length",
        "pattern",
        "range",
        "title",
        "type",
        "url",
        "value-titles",
        "values",
    }
)


def normalise_block(settings: dict[str, str]) -> dict[str, Any]:
    """Normalise one `[namelist:<block>]` section.

    Args:
        settings: The section's settings.

    Returns:
        The normalised block entry, GUI-only material discarded.
    """
    entry: dict[str, Any] = {}
    for key in ("title", "description", "url"):
        if (value := settings.get(key)) is not None:
            entry[key] = collapse_whitespace(value)
    if (compulsory := settings.get("compulsory")) is not None:
        entry["compulsory"] = compulsory.strip().lower() == "true"
    return entry


def git_commit(repo: Path) -> str:
    """Return the checked-out commit of a git repository.

    Args:
        repo: Path to the repository.

    Returns:
        The full commit SHA, or `"unknown"` if git cannot report one.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def build_extract(repo: Path, version: str) -> dict[str, Any]:
    """Build the normalised extract from a local JULES checkout.

    Args:
        repo: Path to the checkout (containing `rose-meta/`).
        version: JULES version directory, e.g. `vn7.9`.

    Returns:
        The extract, ready to be written as JSON.

    Raises:
        FileNotFoundError: If the checkout has no metadata for `version`.
    """
    meta_root = repo / META_DIR
    package = f"{STANDALONE}/{version}"
    sections, sources = load_metadata(meta_root, package)

    fields: dict[str, dict[str, Any]] = {}
    blocks: dict[str, dict[str, Any]] = {}
    discarded: list[str] = []
    for name, settings in sections.items():
        if (match := _FIELD_SECTION_RE.match(name)) is not None:
            fields[f"{match['block']}={match['member']}"] = normalise_field(
                name, settings
            )
        elif (match := _BLOCK_SECTION_RE.match(name)) is not None:
            blocks[match["block"]] = normalise_block(settings)
        else:
            discarded.append(name)

    return {
        "provenance": {
            "upstream_repo": UPSTREAM_REPO,
            "upstream_licence": "BSD-3-Clause",
            "commit": git_commit(repo),
            "extracted": dt.date.today().isoformat(),
            "version": version,
            "sources": [f"{META_DIR}/{source}/rose-meta.conf" for source in sources],
            "generated_by": "scripts/rose_meta_extract.py",
        },
        "counts": {
            "sections": len(sections),
            "fields": len(fields),
            "blocks": len(blocks),
            "discarded_sections": len(discarded),
            "rules": sum(len(entry.get("rules", ())) for entry in fields.values()),
        },
        "blocks": blocks,
        "fields": fields,
    }


# --------------------------------------------------------------------------
# The audit
# --------------------------------------------------------------------------


def iter_schema_blocks() -> Iterator[tuple[str, Any]]:
    """Walk `JulesNamelists`, yielding `(block name, model)` for every block.

    Deliberately a third traversal, alongside `julesconf.schemas._base.
    iter_leaf_fields` and `tests/conftest.py::walk_fields`. Those two yield leaf
    fields only, so a block julesconf models but has no fields for yet —
    `jules_overbank_props` is one — would be invisible to them, and the audit
    would report it as agreeing with the metadata when it holds nothing at all.

    Yields:
        `(block name, model class)` pairs, in declaration order.
    """
    from julesconf.schemas import JulesNamelists
    from julesconf.schemas._base import NamelistModel

    def walk(model: type[NamelistModel]) -> Iterator[tuple[str, Any]]:
        for name, info in model.model_fields.items():
            for candidate in (info.annotation, *get_args(info.annotation)):
                if isinstance(candidate, type) and issubclass(candidate, NamelistModel):
                    children = list(walk(candidate))
                    if children:
                        yield from children
                    else:
                        yield name, candidate
                    break

    yield from walk(JulesNamelists)


def field_bounds(info: FieldInfo) -> tuple[float | None, float | None]:
    """Return the `(minimum, maximum)` a pydantic field constrains its value to.

    Constraints may sit on the field itself (`Fraction`), or inside a list's
    item annotation (`list[Annotated[float, Field(ge=0)]] | None`), so the whole
    annotation is searched.

    Args:
        info: The field to inspect.

    Returns:
        The tightest lower and upper bound found, either being `None` when the
        field is unbounded in that direction.
    """
    low: float | None = None
    high: float | None = None

    def note(meta: Any) -> None:
        nonlocal low, high
        for attr in ("ge", "gt"):
            value = getattr(meta, attr, None)
            if value is not None:
                low = value if low is None else max(low, value)
        for attr in ("le", "lt"):
            value = getattr(meta, attr, None)
            if value is not None:
                high = value if high is None else min(high, value)

    def visit(annotation: Any) -> None:
        for meta in getattr(annotation, "metadata", ()):
            note(meta)
            visit(meta)
        for arg in get_args(annotation):
            visit(arg)

    for meta in info.metadata:
        note(meta)
        visit(meta)
    visit(info.annotation)
    return low, high


def field_enum(info: FieldInfo) -> type[IntEnum] | None:
    """Return the `IntEnum` a field is typed as, if any.

    Args:
        info: The field to inspect.

    Returns:
        The enum class, or `None` if the field is not an enum.
    """
    for candidate in (info.annotation, *get_args(info.annotation)):
        if isinstance(candidate, type) and issubclass(candidate, IntEnum):
            return candidate
    return None


def len_rule_dims(entry: dict[str, Any]) -> list[tuple[str, str]]:
    """Return the dimensions a field's `len(this) != …` rules require.

    Args:
        entry: A normalised field entry.

    Returns:
        `(block, dim)` pairs, one per matching rule. Compound expressions such
        as `len(this) != (npft + nnvg)` do not match and are omitted.
    """
    dims = []
    for rule in entry.get("rules", ()):
        if rule["kind"] != "fail-if":
            continue
        if (match := _LEN_RULE_RE.match(rule["expression"])) is not None:
            dims.append((match["block"], match["dim"]))
    return dims


@dataclass
class Audit:
    """The result of comparing an extract against the julesconf schemas.

    Attributes:
        metadata_only_blocks: Blocks the metadata describes and we do not model.
        schema_only_blocks: Blocks we model that vn7.9 metadata does not
            describe.
        missing_fields: Members of shared blocks that we do not model, by block.
        extra_fields: Members we model that vn7.9 metadata does not describe, by
            block.
        bounds_stricter: Fields where our constraints reject values a numeric
            metadata `range=` permits. Contradictions, and the strongest signal
            of a bug in our schemas.
        bounds_unspecified: Fields we constrain that the metadata gives no
            `range=` for. Usually a bound taken from the user guide rather than
            the metadata, but `jules_cropparm=delta_io` shows the class can hide
            a real bug.
        bounds_looser: Fields where the metadata is more restrictive than we
            are, i.e. validation we could add.
        bounds_expression: Fields whose `range=` is an expression rather than a
            list of intervals, so it cannot be compared numerically.
        enum_mismatches: Fields whose `values=` list disagrees with our IntEnum.
        list_len_mismatches: Fields whose `len(this) != …` rule disagrees with
            our `ListLen` annotation.
        list_len_unchecked: Fields carrying such a rule for which we hold no
            `ListLen`.
        counts: Headline figures for the report.
    """

    metadata_only_blocks: list[str] = field(default_factory=list)
    schema_only_blocks: list[str] = field(default_factory=list)
    missing_fields: dict[str, list[str]] = field(default_factory=dict)
    extra_fields: dict[str, list[str]] = field(default_factory=dict)
    bounds_stricter: list[str] = field(default_factory=list)
    bounds_unspecified: list[str] = field(default_factory=list)
    bounds_looser: list[str] = field(default_factory=list)
    bounds_expression: list[str] = field(default_factory=list)
    enum_mismatches: list[str] = field(default_factory=list)
    list_len_mismatches: list[str] = field(default_factory=list)
    list_len_unchecked: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def render(self) -> str:
        """Render the audit as a plain-text report.

        Returns:
            The report, ending in a newline.
        """
        lines = ["julesconf schema audit against JULES rose metadata", ""]
        for key, value in self.counts.items():
            lines.append(f"  {key.replace('_', ' '):<34} {value}")

        def block(title: str, items: list[str]) -> None:
            lines.extend(["", f"{title} ({len(items)})"])
            lines.extend(f"  {item}" for item in items or ["- none -"])

        block("Blocks in metadata but not in schemas", self.metadata_only_blocks)
        block("Blocks in schemas but not in vn7.9 metadata", self.schema_only_blocks)

        total = sum(len(v) for v in self.missing_fields.values())
        lines.extend(["", f"Members missing from schemas ({total})"])
        for name, members in sorted(
            self.missing_fields.items(), key=lambda kv: (-len(kv[1]), kv[0])
        ):
            lines.append(f"  {name:<36} {len(members):>3}  {', '.join(members)}")

        total = sum(len(v) for v in self.extra_fields.values())
        lines.extend(["", f"Members in schemas but not in vn7.9 metadata ({total})"])
        for name, members in sorted(self.extra_fields.items()):
            lines.append(f"  {name:<36} {len(members):>3}  {', '.join(members)}")

        block("Bounds tighter than the metadata's range", self.bounds_stricter)
        block("Bounds the metadata imposes that we do not", self.bounds_looser)
        block("Bounds we impose where the metadata has none", self.bounds_unspecified)
        block("Ranges the metadata states as an expression", self.bounds_expression)
        block("Enumerations that disagree", self.enum_mismatches)
        block("List lengths that disagree", self.list_len_mismatches)
        block("List length rules we do not model", self.list_len_unchecked)
        return "\n".join(lines) + "\n"


def _postponed(block: str, postponed: frozenset[str]) -> bool:
    """Return whether a metadata block belongs to a postponed extension."""
    return (
        block in postponed
        or block in POSTPONED_META_BLOCKS
        or block.startswith("cable_")
    )


def run_audit(extract: dict[str, Any]) -> Audit:
    """Compare an extract against the julesconf schemas.

    Args:
        extract: A loaded extract, as written by `extract`.

    Returns:
        The audit result.
    """
    from julesconf.schemas import POSTPONED_NAMELISTS

    meta_fields: dict[str, dict[str, dict[str, Any]]] = {}
    for entry in extract["fields"].values():
        meta_fields.setdefault(entry["block"], {})[entry["member"]] = entry
    meta_blocks = {
        name
        for name in set(extract["blocks"]) | set(meta_fields)
        if not _postponed(name, POSTPONED_NAMELISTS)
    }

    schema_blocks = dict(iter_schema_blocks())
    audit = Audit(
        metadata_only_blocks=sorted(meta_blocks - set(schema_blocks)),
        schema_only_blocks=sorted(set(schema_blocks) - meta_blocks),
    )

    shared = sorted(meta_blocks & set(schema_blocks))
    meta_members = 0
    our_members = 0
    for name in shared:
        members = meta_fields.get(name, {})
        ours = schema_blocks[name].model_fields
        meta_members += len(members)
        our_members += len(ours)
        if missing := sorted(set(members) - set(ours)):
            audit.missing_fields[name] = missing
        if extra := sorted(set(ours) - set(members)):
            audit.extra_fields[name] = extra

        for member in sorted(set(members) & set(ours)):
            _compare_field(audit, name, member, members[member], ours[member])

    audit.counts = {
        "blocks_in_metadata": len(meta_blocks),
        "blocks_in_schemas": len(schema_blocks),
        "blocks_shared": len(shared),
        "members_in_metadata": meta_members,
        "members_in_schemas": our_members,
        "members_missing": sum(len(v) for v in audit.missing_fields.values()),
        "members_extra": sum(len(v) for v in audit.extra_fields.values()),
        "bounds_stricter_than_metadata": len(audit.bounds_stricter),
        "bounds_looser_than_metadata": len(audit.bounds_looser),
        "bounds_without_metadata_range": len(audit.bounds_unspecified),
        "bounds_metadata_expression": len(audit.bounds_expression),
        "enum_mismatches": len(audit.enum_mismatches),
        "list_len_mismatches": len(audit.list_len_mismatches),
        "list_len_rules_not_modelled": len(audit.list_len_unchecked),
    }
    return audit


def _describe_bounds(low: float | None, high: float | None) -> str:
    """Render a pair of bounds for the report, empty if there are none.

    Args:
        low: Lower bound, or `None`.
        high: Upper bound, or `None`.

    Returns:
        A string such as `">= 0.0, <= 1.0"`, or `""` if unbounded both ways.
    """
    parts = []
    if low is not None:
        parts.append(f">= {low}")
    if high is not None:
        parts.append(f"<= {high}")
    return ", ".join(parts)


def _compare_field(
    audit: Audit, block: str, member: str, entry: dict[str, Any], info: FieldInfo
) -> None:
    """Compare one member's metadata against its pydantic field.

    Args:
        audit: The audit to record findings in.
        block: Name of the namelist block.
        member: Name of the member.
        entry: The normalised metadata entry.
        info: Our field.
    """
    from julesconf.schemas._namelists import find_list_len

    where = f"{block}={member}"
    raw_range = entry.get("range")
    segments = entry.get("range_segments")
    our_low, our_high = field_bounds(info)
    ours = _describe_bounds(our_low, our_high)

    if raw_range is not None and not segments:
        if ours:
            audit.bounds_expression.append(
                f"{where}: metadata {raw_range}, ours {ours}"
            )
    elif segments:
        lows = [seg["min"] for seg in segments]
        highs = [seg["max"] for seg in segments]
        meta_low = None if any(value is None for value in lows) else min(lows)
        meta_high = None if any(value is None for value in highs) else max(highs)
        if (our_low is not None and (meta_low is None or our_low > meta_low)) or (
            our_high is not None and (meta_high is None or our_high < meta_high)
        ):
            audit.bounds_stricter.append(f"{where}: metadata {raw_range}, ours {ours}")
        if (meta_low is not None and (our_low is None or our_low < meta_low)) or (
            meta_high is not None and (our_high is None or our_high > meta_high)
        ):
            audit.bounds_looser.append(
                f"{where}: metadata {raw_range}, ours {ours or 'unbounded'}"
            )
    elif ours:
        audit.bounds_unspecified.append(f"{where}: no metadata range, ours {ours}")

    enum = field_enum(info)
    if enum is not None and (values := entry.get("values")):
        try:
            expected = {int(value) for value in values}
        except ValueError:
            expected = set()
        if expected:
            our_values = {int(value) for value in enum}
            if expected != our_values:
                audit.enum_mismatches.append(
                    f"{where}: metadata {sorted(expected)}, ours {sorted(our_values)}"
                )

    list_len = find_list_len(info)
    for _, dim in len_rule_dims(entry):
        if list_len is None:
            audit.list_len_unchecked.append(f"{where}: metadata requires {dim}")
        elif dim not in (list_len.dim, *list_len.tolerates):
            accepted = ", ".join((list_len.dim, *list_len.tolerates))
            audit.list_len_mismatches.append(
                f"{where}: metadata {dim}, ours {accepted}"
            )


# --------------------------------------------------------------------------
# The disposition lockfile
# --------------------------------------------------------------------------

DEFAULT_DISPOSITION = Path("tests/data/rose_meta/rules_disposition.toml")
"""Where the committed disposition lockfile lives."""

DISPOSITION_HEADER = """\
# Disposition of every conditional rule in the JULES vn7.9 rose metadata.
#
# Generated by `python scripts/rose_meta_extract.py disposition`, then curated
# by hand. Regenerating preserves the `status`, `where` and `reason` of every
# entry whose rule still exists; it refreshes `hash`, adds newly-appeared rules
# with an auto-assigned status, and drops entries whose rule has gone.
#
# One entry per rule id in `vn7.9.json`. `hash` is the digest of the rule's
# normalised expression, so an edit to the extract that is not reflected here
# fails `tests/schemas/test_rose_rule_coverage.py`.
#
# status vocabulary
# -----------------
#   implemented        julesconf enforces the rule. `where` names the
#                      validator, as `<module>.<Model>.<method>`.
#   covered-by-listlen a `len(this) != <dim>` rule enforced generically by the
#                      `ListLen` machinery rather than by its own validator.
#                      `where` names the annotation.
#   out-of-scope       the rule belongs to a namelist julesconf deliberately
#                      does not model (see `POSTPONED_NAMELISTS`).
#   todo               looked at, not implemented. `reason` says why. This is a
#                      tracked backlog and does NOT fail the coverage test —
#                      the gate is only that every upstream rule appears here.
"""

_LEN_DIM_RE = re.compile(r"namelist:(?P<block>\w+)=(?P<dim>\w+)")

DISPOSITION_STATUSES = frozenset(
    {"implemented", "covered-by-listlen", "out-of-scope", "todo"}
)
"""The statuses a disposition entry may carry."""


def _len_rule_dim(expression: str) -> str | None:
    """Return the dimension a `len(this) != …` expression compares against.

    Args:
        expression: A normalised rule expression.

    Returns:
        The dimension name, `"ntype"` for the `npft + nnvg` spelling, or `None`
        if the expression is not a plain list-length rule.
    """
    body = expression.partition("!=")
    if not body[1] or not body[0].strip().startswith("len(this)"):
        return None
    dims = [match["dim"] for match in _LEN_DIM_RE.finditer(body[2])]
    if len(dims) == 1:
        return dims[0]
    if dims == ["npft", "nnvg"] and "+" in body[2]:
        return "ntype"
    return None


def _schema_list_len(block: str, member: str) -> Any:
    """Return the `ListLen` julesconf holds for a member, if it models one."""
    from julesconf.schemas._namelists import find_list_len

    for name, model in iter_schema_blocks():
        if name != block:
            continue
        info = model.model_fields.get(member)
        return None if info is None else find_list_len(info)
    return None


def auto_status(entry: dict[str, Any], rule: dict[str, Any]) -> dict[str, str]:
    """Classify a rule that the lockfile does not yet mention.

    Args:
        entry: The normalised field entry the rule belongs to.
        rule: The rule itself.

    Returns:
        A disposition entry body, without the `hash`.
    """
    from julesconf.schemas import POSTPONED_NAMELISTS

    block, member = entry["block"], entry["member"]
    if _postponed(block, POSTPONED_NAMELISTS):
        return {"status": "out-of-scope", "reason": f"postponed namelist ({block})"}

    dim = _len_rule_dim(rule["expression"])
    if dim is not None:
        list_len = _schema_list_len(block, member)
        if list_len is not None and dim in (list_len.dim, *list_len.tolerates):
            return {"status": "covered-by-listlen", "where": f"ListLen({dim!r})"}

    if not any(name == block for name, _ in iter_schema_blocks()):
        return {"status": "todo", "reason": f"julesconf does not model {block}"}
    if _schema_member_missing(block, member):
        return {
            "status": "todo",
            "reason": f"julesconf does not model {block}={member}",
        }
    return {"status": "todo", "reason": "not yet implemented"}


def _schema_member_missing(block: str, member: str) -> bool:
    """Return whether julesconf models `block` but not its `member`."""
    for name, model in iter_schema_blocks():
        if name == block:
            return member not in model.model_fields
    return False


def build_disposition(
    extract: dict[str, Any], existing: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    """Merge the rules in an extract into an existing disposition lockfile.

    Args:
        extract: A loaded extract, as written by `extract`.
        existing: The lockfile as loaded from disk, or `{}`.

    Returns:
        A `(entries, counts)` pair. `entries` is keyed by rule id and sorted;
        `counts` reports the status breakdown plus `added` and `removed`.
    """
    entries: dict[str, dict[str, str]] = {}
    counts: dict[str, int] = dict.fromkeys(sorted(DISPOSITION_STATUSES), 0)
    counts["added"] = 0

    for entry in extract["fields"].values():
        for rule in entry.get("rules", ()):
            rule_id = rule["id"]
            previous = existing.get(rule_id)
            if previous is None:
                body = auto_status(entry, rule)
                counts["added"] += 1
            else:
                body = {k: v for k, v in previous.items() if k != "hash"}
            body["hash"] = rule["hash"]
            entries[rule_id] = body
            counts[body["status"]] = counts.get(body["status"], 0) + 1

    counts["removed"] = len(set(existing) - set(entries))
    return {key: entries[key] for key in sorted(entries)}, counts


def render_disposition(entries: dict[str, dict[str, str]]) -> str:
    """Render the disposition lockfile as TOML.

    Written by hand rather than with `tomli_w` so the header comment survives
    and the key order within an entry stays `status`, `where`, `reason`,
    `hash`.

    Args:
        entries: Disposition entries, keyed by rule id.

    Returns:
        The file contents.
    """
    lines = [DISPOSITION_HEADER]
    for rule_id, body in entries.items():
        lines.append(f'\n["{rule_id}"]')
        for key in ("status", "where", "reason", "hash"):
            if (value := body.get(key)) is not None:
                escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key} = "{escaped}"')
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Drift between two extracts
# --------------------------------------------------------------------------


def _rules_by_id(extract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index every rule in an extract by its id."""
    return {
        rule["id"]: rule
        for entry in extract["fields"].values()
        for rule in entry.get("rules", ())
    }


def _describe_rule(rule: dict[str, Any], disposition: dict[str, Any]) -> str:
    """Render one rule as a Markdown bullet, with its disposition and reason."""
    status = disposition.get(rule["id"], {}).get("status", "no disposition entry")
    line = f"- `{rule['id']}` (_{status}_)\n  - `{rule['expression']}`"
    if reason := rule.get("reason"):
        line += f"\n  - upstream comment: {reason}"
    return line


def render_drift(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    disposition: dict[str, Any],
) -> tuple[str, bool]:
    """Compare two extracts and render the difference as Markdown.

    Args:
        baseline: The committed extract.
        candidate: A freshly built extract from upstream `main`.
        disposition: The lockfile, so each affected rule is reported with what
            julesconf currently does about it.

    Returns:
        A `(report, drifted)` pair. `report` is Markdown; `drifted` is `False`
        when the two extracts declare exactly the same rules.
    """
    before, after = _rules_by_id(baseline), _rules_by_id(candidate)
    added = [after[k] for k in sorted(set(after) - set(before))]
    removed = [before[k] for k in sorted(set(before) - set(after))]
    changed = [
        (before[k], after[k])
        for k in sorted(set(before) & set(after))
        if before[k]["hash"] != after[k]["hash"]
    ]

    version = candidate["provenance"]["version"]
    commit = candidate["provenance"]["commit"]
    lines = [
        f"The JULES `{version}` rose metadata has changed upstream since"
        f" `tests/data/rose_meta/{version}.json` was generated.",
        "",
        f"- upstream commit: `{commit}`",
        f"- added: {len(added)}  removed: {len(removed)}  changed: {len(changed)}",
        "",
        "Each rule below is annotated with its current status in"
        " `tests/data/rose_meta/rules_disposition.toml`. Decide per rule whether"
        " to implement it, defer it, or rule it out of scope, then refresh both"
        " files:",
        "",
        "```",
        "python scripts/rose_meta_extract.py extract",
        "python scripts/rose_meta_extract.py disposition",
        "```",
    ]

    for title, rules in (("Added", added), ("Removed", removed)):
        if rules:
            lines += ["", f"## {title} ({len(rules)})", ""]
            lines += [_describe_rule(rule, disposition) for rule in rules]

    if changed:
        lines += ["", f"## Changed ({len(changed)})", ""]
        for old, new in changed:
            lines.append(_describe_rule(new, disposition))
            lines.append(f"  - was: `{old['expression']}`")

    return "\n".join(lines) + "\n", bool(added or removed or changed)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def write_output(path: Path | None, text: str) -> None:
    """Write text to a file, or to stdout if `path` is `None`.

    Args:
        path: Destination, or `None` for stdout.
        text: The text to write.
    """
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _destination(value: str) -> Path | None:
    """Interpret an `-o` value, `-` meaning stdout."""
    return None if value == "-" else Path(value)


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface.

    Args:
        argv: Arguments, defaulting to `sys.argv[1:]`.

    Returns:
        A process exit status.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser(
        "extract", help="write a normalised JSON extract of the rose metadata"
    )
    extract_parser.add_argument(
        "--jules-repo",
        type=Path,
        default=DEFAULT_REPO,
        help=f"local checkout of {UPSTREAM_REPO} (default: %(default)s)",
    )
    extract_parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help="JULES version (default: %(default)s)",
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_EXTRACT),
        help="output path, or - for stdout",
    )

    audit_parser = subparsers.add_parser(
        "audit", help="compare an extract against the julesconf schemas"
    )
    audit_parser.add_argument(
        "--extract",
        type=Path,
        default=DEFAULT_EXTRACT,
        help="extract to audit against (default: %(default)s)",
    )
    audit_parser.add_argument(
        "-o", "--output", default="-", help="output path, or - for stdout"
    )

    disposition_parser = subparsers.add_parser(
        "disposition", help="refresh the rule disposition lockfile"
    )
    disposition_parser.add_argument(
        "--extract",
        type=Path,
        default=DEFAULT_EXTRACT,
        help="extract to read rules from (default: %(default)s)",
    )
    disposition_parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_DISPOSITION),
        help="output path, or - for stdout",
    )

    drift_parser = subparsers.add_parser(
        "drift", help="compare a freshly built extract against the committed one"
    )
    drift_parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_EXTRACT,
        help="committed extract (default: %(default)s)",
    )
    drift_parser.add_argument(
        "candidate", type=Path, help="freshly built extract to compare against"
    )
    drift_parser.add_argument(
        "--disposition",
        type=Path,
        default=DEFAULT_DISPOSITION,
        help="lockfile to annotate the report with (default: %(default)s)",
    )
    drift_parser.add_argument(
        "-o", "--output", default="-", help="output path, or - for stdout"
    )

    args = parser.parse_args(argv)

    if args.command == "drift":
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        disposition: dict[str, Any] = {}
        if args.disposition.is_file():
            disposition = tomllib.loads(args.disposition.read_text(encoding="utf-8"))
        report, drifted = render_drift(baseline, candidate, disposition)
        if drifted:
            write_output(_destination(args.output), report)
        print(f"drift={'true' if drifted else 'false'}")
        return 0

    if args.command == "disposition":
        extract = json.loads(Path(args.extract).read_text(encoding="utf-8"))
        destination = _destination(args.output)
        existing: dict[str, Any] = {}
        if destination is not None and destination.is_file():
            existing = tomllib.loads(destination.read_text(encoding="utf-8"))
        entries, counts = build_disposition(extract, existing)
        write_output(destination, render_disposition(entries))
        print(
            ", ".join(
                f"{key.replace('-', ' ')} {value}" for key, value in counts.items()
            ),
            file=sys.stderr,
        )
        return 0

    if args.command == "extract":
        data = build_extract(args.jules_repo, args.version)
        write_output(
            _destination(args.output),
            json.dumps(data, indent=2, sort_keys=True) + "\n",
        )
        counts = data["counts"]
        print(
            f"{counts['sections']} sections, {counts['fields']} fields, "
            f"{counts['blocks']} blocks, {counts['rules']} rules "
            f"from {len(data['provenance']['sources'])} files",
            file=sys.stderr,
        )
        return 0

    extract = json.loads(Path(args.extract).read_text(encoding="utf-8"))
    write_output(_destination(args.output), run_audit(extract).render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
