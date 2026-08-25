"""Gates that the reference docs keep up with the schemas.

The enum and warning pages are hand-written lists of `:::` directives, so
nothing stops a new enum or warning class from being added to the code and
never appearing in the docs. That is how `enums.md` came to be missing 13 of
45 enums without anyone noticing: the page still built, still rendered, and
still looked complete.

These tests follow the anti-drift idiom used by
`test_grouped_models.py::test_generated_model_covers_exactly_its_dims` — assert
the documented set equals the real set, in both directions, so a stale entry
is caught as loudly as a missing one.
"""

import re
from enum import IntEnum
from pathlib import Path

import pytest

import julesconf.schemas as schemas_pkg

DOCS = Path(__file__).parent.parent / "docs" / "api" / "schemas"
SRC = Path(__file__).parent.parent / "src" / "julesconf" / "schemas"


def _documented(page: str) -> set[str]:
    """Return the leaf names of every `:::` directive on a reference page."""
    text = (DOCS / page).read_text()
    return {
        target.rsplit(".", 1)[-1]
        for target in re.findall(r"^::: +(julesconf\.[\w.]+)", text, re.M)
    }


def _defined(base: type) -> set[str]:
    """Return every public subclass of `base` declared in the schema modules."""
    found = set()
    for path in SRC.glob("*.py"):
        for name in re.findall(
            rf"^class (\w+)\({base.__name__}\)", path.read_text(), re.M
        ):
            found.add(name)
    return found


def test_every_enum_is_documented():
    """`enums.md` is the discovery surface for what an option accepts."""
    documented, defined = _documented("enums.md"), _defined(IntEnum)
    assert defined - documented == set(), (
        "enums missing from docs/api/schemas/enums.md — a user cannot discover"
        " the member names of an option that is not listed there"
    )


def test_enums_page_has_no_stale_entries():
    documented, defined = _documented("enums.md"), _defined(IntEnum)
    assert documented - defined == set(), (
        "docs/api/schemas/enums.md names enums that no longer exist; the page"
        " will fail to build or silently render nothing"
    )


@pytest.mark.parametrize(
    "name",
    [
        "UnknownNamelistKeyWarning",
        "PostponedNamelistWarning",
        "RepeatedNamelistGroupWarning",
        "InactiveNamelistKeyWarning",
        "DiscouragedValueWarning",
        "ToleratedLengthWarning",
    ],
)
def test_every_warning_is_documented(name):
    """Each warning must be documented, because each is escalated separately.

    The whole point of one class per situation is that a user can turn just
    that one into an error. An undocumented class is one they cannot know to
    filter.
    """
    assert hasattr(schemas_pkg, name), f"{name} is not exported from julesconf.schemas"
    assert name in _documented("warnings.md"), (
        f"{name} is missing from docs/api/schemas/warnings.md"
    )
