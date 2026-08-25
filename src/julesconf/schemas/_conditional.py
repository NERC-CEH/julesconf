"""Helpers for the conditional field rules JULES ships in its rose metadata.

`MetOffice/jules` publishes a machine-readable specification of every namelist
member under `rose-meta/`, and part of that specification is a set of
*conditional* rules relating one member to another. `scripts/rose_meta_extract.py`
normalises them into `tests/data/rose_meta/vn7.9.json`, and they come in two
severities, which julesconf deliberately treats differently:

`fail-if`
:   The configuration is wrong. JULES will misbehave or refuse to run, so the
    rule is raised as a validation error by a `@model_validator(mode="after")`
    on the block it belongs to, or on `JulesNamelists` when it spans blocks.

`trigger`
:   The member is merely *inactive* given the state of some switch. Rose greys
    it out in its config editor; JULES simply ignores it. Setting `kaps` while
    `soil_bgc_model = four_pool` is a configuration smell — the author probably
    believes it is doing something — but it is not an error, so it raises
    `InactiveNamelistKeyWarning` instead.

`warn-if`
:   The value is used, and the run will proceed, but JULES's own authors advise
    against it: a deprecated option, a scheme tuned only for some other
    setting, a value with a surprising physical consequence. This is the one
    severity that says nothing about whether the value takes effect — it does —
    so it raises `DiscouragedValueWarning`.

Which rules are implemented, and which are deliberately not, is tracked in
`tests/data/rose_meta/rules_disposition.toml` and gated by
`tests/schemas/test_rose_rule_coverage.py`.
"""

import warnings
from collections.abc import Iterable
from typing import Any

from pydantic.fields import FieldInfo

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import PerElementDefault

__all__ = [
    "DiscouragedValueWarning",
    "InactiveNamelistKeyWarning",
    "check_group_count",
    "fail_if",
    "is_specified",
    "warn_discouraged",
    "warn_inactive",
]


class InactiveNamelistKeyWarning(UserWarning):
    """A member was given a value that JULES will ignore.

    Many JULES namelist members are only read when some other switch selects
    the scheme they belong to: `kaps` is read only by the single-pool soil
    carbon model, the RFM river parameters only when `i_river_vn = rfm`, the
    bedrock parameters only when `l_bedrock` is true. JULES does not complain
    about the others — it never looks at them — so a value set there does
    nothing at all, which is rarely what the author intended.

    Distinct from `UnknownNamelistKeyWarning`, which concerns a member
    julesconf does not model; from `PostponedNamelistWarning`, which concerns
    a whole namelist file julesconf excludes; and from
    `RepeatedNamelistGroupWarning`, which concerns a group julesconf can only
    hold one of. This concerns a member julesconf models perfectly well and
    JULES will discard, so it is escalated separately:

        import warnings

        from julesconf.schemas import InactiveNamelistKeyWarning

        warnings.simplefilter("error", InactiveNamelistKeyWarning)

    Only a value that *differs from the schema default* is reported, so a
    config that has been round-tripped through `to_namelists` — which writes
    every member julesconf holds a default for — does not produce a warning
    for every inactive member of every unused scheme.
    """


class DiscouragedValueWarning(UserWarning):
    """A value JULES accepts and uses, but which its authors advise against.

    The `warn-if` half of the rose metadata, and the only one of julesconf's
    warnings that does *not* mean something is being ignored or dropped. The
    setting takes effect exactly as written; upstream simply thinks it is a
    poor choice — a deprecated canopy model, a scheme tuned only for some other
    substrate, a value with a physical consequence the author may not have
    intended.

    That distinction matters when deciding what to escalate.
    `UnknownNamelistKeyWarning`, `PostponedNamelistWarning` and
    `RepeatedNamelistGroupWarning` all mean part of the configuration is
    silently lost, and `InactiveNamelistKeyWarning` means part of it does
    nothing. Those are defects in the config *as julesconf handles it*. This
    one is a scientific opinion held by the JULES developers, so a project with
    a considered reason to disagree can filter it alone:

        import warnings

        from julesconf.schemas import DiscouragedValueWarning

        warnings.simplefilter("ignore", DiscouragedValueWarning)

    or, in a pipeline that should not ship a discouraged option, escalate it
    the same way:

        warnings.simplefilter("error", DiscouragedValueWarning)
    """


def warn_discouraged(condition: Any, reason: str) -> None:
    """Warn with `reason` when a rose `warn-if` condition holds.

    The mirror of `fail_if`, for the advisory severity.

    Args:
        condition: The rule's condition, already evaluated.
        reason: The message to warn with. Where upstream supplies a `#` comment
            on the rule, that comment is used verbatim — the JULES developers'
            wording carries their intent better than a paraphrase.
    """
    if condition:
        warnings.warn(reason, DiscouragedValueWarning, stacklevel=3)


def is_specified(model: NamelistModel, member: str) -> bool:
    """Return whether a member holds a value other than its schema default.

    This is julesconf's test for "the author meant this". `model_fields_set`
    is not usable for it: `to_namelist_dict` writes every member julesconf
    holds a default for, so reading those namelists back marks the whole
    config as explicitly set. Comparing against the default instead makes the
    answer stable across a read-write-read cycle.

    Args:
        model: The block holding the member.
        member: Name of the member.

    A list field marked `PerElementDefault` declares its default twice: `None`
    on the field, and a scalar that `to_namelist_dict` repeats to the full
    length of the dimension, because Fortran namelist input does not broadcast.
    Both spellings mean "the author said nothing", so a list whose every
    element is that scalar counts as unspecified too — otherwise a config would
    acquire warnings simply by being written out and read back, which is the
    exact failure this helper exists to prevent.

    Returns:
        `True` if the member exists, is not `None`, and differs from the
        default declared for it.
    """
    field = type(model).model_fields.get(member)
    if field is None:
        return False
    value = getattr(model, member, None)
    if value is None:
        return False
    if value == field.get_default(call_default_factory=True):
        return False
    per_element = _per_element_default(field)
    if per_element is None or not isinstance(value, list):
        return True
    return not all(element == per_element.value for element in value)


def _per_element_default(field: FieldInfo) -> PerElementDefault | None:
    """Return the `PerElementDefault` marking `field`, if it carries one.

    Deliberately a local reimplementation of
    `julesconf.schemas._namelists.find_per_element_default`: `_namelists`
    imports this module, so importing it back would be circular. Like that
    one, it looks only at the outermost `Annotated`, which is where
    `PerElementDefault` has to sit to be seen at all.
    """
    for meta in field.metadata:
        if isinstance(meta, PerElementDefault):
            return meta
    return None


def warn_inactive(
    model: NamelistModel, members: Iterable[str], *, because: str
) -> None:
    """Warn for each specified member that JULES will ignore.

    Implements the `trigger` half of the rose metadata: `members` are the
    rule's targets and `because` describes the switch state that makes them
    inactive.

    Args:
        model: The block holding the members.
        members: Names of the members the trigger governs.
        because: Human-readable statement of why they are inactive, phrased to
            follow "…is ignored because ", e.g. `"l_bedrock is false"`.
    """
    for member in members:
        if is_specified(model, member):
            warnings.warn(
                f"{type(model).__name__}: {member!r} is set but JULES will"
                f" ignore it because {because}",
                InactiveNamelistKeyWarning,
                stacklevel=3,
            )


def check_group_count(
    group: str, blocks: list[Any], count: int | None, *, count_member: str
) -> None:
    """Check a repeated namelist group against the member that counts it.

    JULES reads a repeated group a fixed number of times, given by a member of
    a sibling block: `nprofiles` groups of `JULES_OUTPUT_PROFILE`, `n_datasets`
    of `JULES_PRESCRIBED_DATASET`, `ndry_dep_species` of
    `JULES_DEPOSITION_SPECIES`. The two must agree, and the asymmetry is
    JULES's own:

    - **Too few blocks is fatal.** JULES reads until it has the number it was
      promised and hits the end of the file, so this raises.
    - **Too many is legal and common.** JULES reads the leading `count` groups
      and never looks at the rest. Real rose apps keep spare profiles this way
      — `loobos_jules_es_1p0_deposition` ships seven and sets `nprofiles = 2`.
      The extras are preserved verbatim, and an `InactiveNamelistKeyWarning`
      makes their inertness visible when they actually say something. A surplus
      group that sets nothing — the empty `&jules_prescribed_dataset /`
      placeholder most JULES configs carry — is silent, following the same rule
      as `warn_inactive`: julesconf reports what the author wrote, not what a
      default happens to be.

    This rule is julesconf's own: rose expresses repetition with a
    `duplicate=true` section property rather than in its `fail-if` language, so
    there is no upstream rule to transcribe.

    Args:
        group: The namelist group name, for the messages.
        blocks: The list of blocks read for that group.
        count: The value of the counting member, or `None` if it is unset.
        count_member: `BLOCK::member` naming where the count comes from.

    Raises:
        ValueError: If there are fewer blocks than the count calls for.
    """
    expected = 0 if count is None else count
    unset = " (unset, so taken as 0)" if count is None else ""
    if len(blocks) < expected:
        raise ValueError(
            f"{group} occurs {len(blocks)} time(s) but {count_member} is"
            f" {expected}{unset}; JULES reads {expected} {group} group(s) and"
            " would run out of input. Add the missing group(s), or lower"
            f" {count_member}"
        )
    surplus = [
        block
        for block in blocks[expected:]
        if isinstance(block, NamelistModel)
        and block.model_dump(exclude_defaults=True, exclude_none=True)
    ]
    if surplus:
        warnings.warn(
            f"{group} occurs {len(blocks)} time(s) but {count_member} is"
            f" {expected}{unset}, so JULES will read only the first"
            f" {expected} and ignore the remaining {len(blocks) - expected}."
            " They are kept as written",
            InactiveNamelistKeyWarning,
            stacklevel=3,
        )


def fail_if(condition: Any, reason: str) -> None:
    """Raise `ValueError(reason)` when a rose `fail-if` condition holds.

    Args:
        condition: The rule's condition, already evaluated.
        reason: The message to raise. Where upstream supplies a `#` comment on
            the rule, that comment is used verbatim — the JULES developers'
            wording is better than anything julesconf would invent.

    Raises:
        ValueError: If `condition` is truthy.
    """
    if condition:
        raise ValueError(reason)
