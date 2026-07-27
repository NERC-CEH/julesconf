"""Human-readable rendering of validation failures and warnings.

A raw `pydantic.ValidationError` names a config member by its position in the
model tree — `('jules_soil', 'jules_soil', 'dzsoil_io')` — which is not how a
JULES user thinks about their configuration. They think in terms of a file, a
namelist group, and a member:

    jules_soil.nml  JULES_SOIL  dzsoil_io
      dzsoil_io has 3 element(s), expected sm_levels=4

`ConfigError` is that translation, and `format_validation_error` renders a
whole `ValidationError` as the block above. The mapping is direct: the fields
of `julesconf.schemas.JulesNamelists` are named one-to-one after the `.nml`
files, and JULES writes namelist group names in upper case.

The warning half does the same job for the four warning categories julesconf
raises. They differ in consequence — some are advisory, some mean the config
cannot be represented and something will be silently dropped — so
`group_warnings` sorts them by that distinction rather than leaving Python's
warning machinery to print them one line at a time in arrival order.

Nothing here depends on the CLI: the module renders plain text and returns
structured data, so library callers and tests can use it directly.
"""

from __future__ import annotations

import dataclasses
import textwrap
import warnings
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

from pydantic import ValidationError

__all__ = [
    "WARNING_KINDS",
    "ConfigError",
    "WarningGroup",
    "WarningKind",
    "format_config_errors",
    "format_cross_namelist_skipped",
    "format_validation_error",
    "format_warnings",
    "group_warnings",
    "iter_config_errors",
]

_MESSAGE_PREFIXES = ("Value error, ", "Assertion failed, ")

CROSS_NAMELIST = "<cross-namelist>"
"""Stand-in location for an error raised by a whole-config validator."""

WIDTH = 79
"""Column to wrap report prose at.

The reports are wrapped here rather than left to the terminal so that piping
the output to a file, or capturing it in a test, gives the same layout as
reading it interactively.
"""


def _wrap(text: str, indent: str, *, hanging: str | None = None) -> list[str]:
    """Wrap one paragraph to `WIDTH`, indenting every line."""
    return textwrap.wrap(
        text,
        width=WIDTH,
        initial_indent=indent,
        subsequent_indent=hanging if hanging is not None else indent,
    ) or [indent.rstrip()]


@dataclasses.dataclass(frozen=True)
class ConfigError:
    """One validation failure, located in JULES's own terms.

    Attributes:
        namelist: The `.nml` file the failure is in, or `None` if the error
            came from a validator spanning the whole config.
        block: The namelist group, upper-cased as JULES writes it, or `None`.
            A group that occurs more than once in its file carries its 1-based
            occurrence number, as `JULES_OUTPUT_PROFILE[3]`.
        member: The namelist member, with any list index appended as
            `member[3]`, or `None` when the failing validator is attached to
            the block rather than to one member.
        message: The failure itself, with pydantic's framing removed.
        loc: The original pydantic error location, kept for callers that need
            to correlate back to the raw error.
    """

    namelist: str | None
    block: str | None
    member: str | None
    message: str
    loc: tuple[str | int, ...] = ()

    @property
    def location(self) -> str:
        """The `file  BLOCK  member` header, as a single string."""
        parts = [part for part in (self.namelist, self.block, self.member) if part]
        return "  ".join(parts) if parts else CROSS_NAMELIST

    def __str__(self) -> str:
        """Render as the two-line `location` / indented `message` form."""
        return f"{self.location}\n  {self.message}"


def _clean_message(error: Mapping[str, Any]) -> str:
    """Turn one pydantic error dict into a message a JULES user can act on."""
    message = str(error.get("msg", ""))
    for prefix in _MESSAGE_PREFIXES:
        if message.startswith(prefix):
            message = message[len(prefix) :]

    # Pydantic phrases an IntEnum miss as "Input should be 1, 2 or 3", which
    # says what is wanted but not what was given. Both matter here: the value
    # came from a namelist the user wrote.
    if error.get("type") == "enum":
        expected = str(error.get("ctx", {}).get("expected", "")).replace(" or ", ", ")
        given = error.get("input")
        return f"{given!r} is not a valid value; valid values: {expected}"

    return message


def _infer_member(error: Mapping[str, Any], message: str) -> str | None:
    """Guess which member a block-level validator is complaining about.

    A validator attached to the whole block reports a location that stops at
    the block, but its message almost always opens with the member's name —
    `dzsoil_io has 3 element(s), expected sm_levels=4`. Recovering it puts the
    error in the same three-part form as every other one. The guess is only
    accepted when the leading word is genuinely a member of the block that was
    validated, so a message like `Can't use 1-pool with TRIFFID` is left alone.
    """
    members = error.get("input")
    if not isinstance(members, dict):
        return None
    first = message.split(" ", 1)[0]
    return first if first in members else None


def _split_loc(
    loc: Sequence[str | int], error: Mapping[str, Any], message: str
) -> tuple[str | None, str | None, str | None]:
    """Split a pydantic location into namelist file, block and member.

    A *repeated* group (`jules_output_profile`, …) puts an integer straight
    after the block name, since julesconf models it as a list of blocks. That
    index belongs with the block, not the member, and is displayed **1-based**
    — `JULES_OUTPUT_PROFILE[3]` is the third group in the file — to match how
    JULES and rose number the occurrences (`[namelist:jules_output_profile(3)]`).
    Indices *within* a member stay as pydantic reports them, 0-based, because
    they index a Python list the user's TOML wrote directly.
    """
    if not loc:
        return None, None, None

    namelist = f"{loc[0]}.nml" if isinstance(loc[0], str) else str(loc[0])
    block = str(loc[1]).upper() if len(loc) > 1 else None

    rest = loc[2:]
    if rest and isinstance(rest[0], int):
        block = f"{block}[{rest[0] + 1}]"
        rest = rest[1:]

    if not rest:
        return namelist, block, _infer_member(error, message)

    member = str(rest[0])
    for index in rest[1:]:
        member = f"{member}[{index}]"
    return namelist, block, member


def iter_config_errors(exc: ValidationError) -> Iterator[ConfigError]:
    """Translate a `ValidationError` into located, readable errors.

    Args:
        exc: The exception raised by validating a JULES configuration.

    Yields:
        One `ConfigError` per underlying pydantic error, in the order pydantic
        reports them.
    """
    for error in exc.errors():
        loc = tuple(error.get("loc", ()))
        message = _clean_message(error)
        namelist, block, member = _split_loc(loc, error, message)
        yield ConfigError(
            namelist=namelist,
            block=block,
            member=member,
            message=message,
            loc=loc,
        )


def format_validation_error(exc: ValidationError) -> str:
    """Render a `ValidationError` as a readable report.

    Args:
        exc: The exception raised by validating a JULES configuration.

    Returns:
        A multi-line report, one indented `file  BLOCK  member` stanza per
        error, headed by the error count.
    """
    return format_config_errors(iter_config_errors(exc))


def format_config_errors(errors: Iterable[ConfigError]) -> str:
    """Render already-translated errors as a readable report.

    Args:
        errors: The errors to render.

    Returns:
        The same report `format_validation_error` produces.
    """
    errors = list(errors)
    plural = "" if len(errors) == 1 else "s"
    lines = [f"Validation failed ({len(errors)} error{plural}):", ""]
    for error in errors:
        lines.append(f"  {error.location}")
        lines.extend(_wrap(error.message, "    ", hanging="      "))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_cross_namelist_skipped(
    directory_hint: str = "the namelists directory",
) -> str:
    """Render the notice that only one namelist file was checked.

    Validating a single file runs that namelist's own rules and nothing else.
    The rules that were not run are exactly the ones an error report locates as
    `<cross-namelist>`, so the notice names them the same way: a reader who has
    seen one report can tell which half of the checking they are missing.

    Args:
        directory_hint: How to refer to the whole configuration in the closing
            suggestion.

    Returns:
        A wrapped, multi-line notice ending in a newline.
    """
    paragraphs = [
        f"Checked this file alone. The {CROSS_NAMELIST} rules were skipped:"
        " the list lengths tied to npft, ncpft, nnvg and ntype, which are"
        " declared in jules_surface_types.nml, and the consistency rules that"
        " read switches from more than one namelist.",
        "This file passing does not mean the configuration is valid. Run"
        f" julesconf validate on {directory_hint} to run those checks too.",
    ]
    return "\n\n".join("\n".join(_wrap(text, "")) for text in paragraphs) + "\n"


@dataclasses.dataclass(frozen=True)
class WarningKind:
    """How one category of julesconf warning should be presented.

    Attributes:
        label: The severity band — `"data loss"` or `"advisory"`.
        explanation: What the category means for the user's config.
        priority: Tie-break for the report order; lower is shown first.
            `RepeatedNamelistGroupWarning` is promoted above the other
            data-loss categories because it is a known modelling gap rather
            than something the user can fix by editing their config.
    """

    label: str
    explanation: str
    priority: int = 1

    @property
    def is_data_loss(self) -> bool:
        """Whether this category means something is silently dropped."""
        return self.label == "data loss"


WARNING_KINDS: dict[str, WarningKind] = {
    "RepeatedNamelistGroupWarning": WarningKind(
        "data loss",
        "This group occurred more than once and julesconf models a single "
        "block of it, so all but the first are dropped and writing the config "
        "back out loses them. The groups JULES itself repeats -- output "
        "profiles, prescribed datasets, deposition species -- are modelled as "
        "lists and are not affected.",
        priority=0,
    ),
    "UnknownNamelistKeyWarning": WarningKind(
        "data loss",
        "These members are not in julesconf's schemas and are ignored, so "
        "writing the config back out drops them.",
    ),
    "PostponedNamelistWarning": WarningKind(
        "data loss",
        "julesconf deliberately does not model these namelists. They are not "
        "validated and will not be written.",
    ),
    "InactiveNamelistKeyWarning": WarningKind(
        "advisory",
        "JULES will not read these members given the switches this config "
        "sets. They are harmless, but they are probably not doing what the "
        "author intended.",
    ),
}
"""Presentation metadata for each warning category julesconf raises."""

_UNKNOWN_KIND = WarningKind("advisory", "", priority=2)


@dataclasses.dataclass(frozen=True)
class WarningGroup:
    """All warnings of one category, with their presentation metadata.

    Attributes:
        category: The warning class name.
        kind: How the category should be presented.
        messages: The distinct messages seen, in first-seen order.
        count: How many warnings were raised, including duplicates.
    """

    category: str
    kind: WarningKind
    messages: list[str]
    count: int


def group_warnings(
    caught: Iterable[warnings.WarningMessage],
) -> list[WarningGroup]:
    """Group recorded warnings by category, data-loss categories first.

    Args:
        caught: The warnings recorded by `warnings.catch_warnings(record=True)`.

    Returns:
        One `WarningGroup` per category seen, ordered with the categories that
        mean silent data loss first and, within a band, most frequent first.
    """
    counts: dict[str, int] = {}
    messages: dict[str, list[str]] = {}
    for item in caught:
        category = item.category.__name__
        counts[category] = counts.get(category, 0) + 1
        seen = messages.setdefault(category, [])
        text = str(item.message)
        if text not in seen:
            seen.append(text)

    groups = [
        WarningGroup(
            category=category,
            kind=WARNING_KINDS.get(category, _UNKNOWN_KIND),
            messages=messages[category],
            count=count,
        )
        for category, count in counts.items()
    ]
    groups.sort(
        key=lambda group: (
            not group.kind.is_data_loss,
            group.kind.priority,
            -group.count,
        )
    )
    return groups


def format_warnings(groups: Iterable[WarningGroup], *, max_messages: int = 5) -> str:
    """Render grouped warnings as a readable report.

    Args:
        groups: The groups to render, as returned by `group_warnings`.
        max_messages: How many distinct messages to show per category before
            summarising the rest.

    Returns:
        A multi-line report, or the empty string if there is nothing to report.
    """
    groups = list(groups)
    if not groups:
        return ""

    total = sum(group.count for group in groups)
    plural = "" if total == 1 else "s"
    lines = [f"{total} warning{plural}:", ""]
    for group in groups:
        lines.append(f"  {group.category} ({group.count}) -- {group.kind.label}")
        if group.kind.explanation:
            lines.extend(_wrap(group.kind.explanation, "    "))
        for message in group.messages[:max_messages]:
            lines.extend(_wrap(message, "    - ", hanging="      "))
        remaining = len(group.messages) - max_messages
        if remaining > 0:
            lines.append(f"    - ... and {remaining} more")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
