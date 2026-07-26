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

Which rules are implemented, and which are deliberately not, is tracked in
`tests/data/rose_meta/rules_disposition.toml` and gated by
`tests/schemas/test_rose_rule_coverage.py`.
"""

import warnings
from collections.abc import Iterable
from typing import Any

from julesconf.schemas._base import NamelistModel

__all__ = ["InactiveNamelistKeyWarning", "fail_if", "is_specified", "warn_inactive"]


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
    return bool(value != field.get_default(call_default_factory=True))


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
