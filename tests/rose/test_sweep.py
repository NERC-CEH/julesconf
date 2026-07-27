"""Convert and validate every JULES rose-stem app, not just the vendored ten.

This is the wide net behind the narrow one. `tests/data/rose_apps/` vendors
ten apps so the suite is hermetic; this module runs the same pipeline over
all of `reference/jules/rose-stem/app/`, which is a gitignored sparse clone
and is absent on CI runners and most checkouts. Every test here is skipped
when it is missing.

Obtain the checkout with:

    git clone --filter=blob:none --sparse \\
        https://github.com/MetOffice/jules reference/jules
    git -C reference/jules sparse-checkout set rose-meta rose-stem

Nothing is hardcoded about which apps exist: the sweep enumerates whatever
the checkout holds, so a newer upstream commit that adds or removes apps
changes the tally rather than breaking the test.
"""

import contextlib
import warnings
from pathlib import Path

import f90nml
import pydantic
import pytest

from julesconf.config import namelist_to_dict
from julesconf.rose import RoseApp, UnsupportedSourceError, rose_to_namelists
from julesconf.schemas import JulesNamelists

JULES_CHECKOUT = Path(__file__).resolve().parents[2] / "reference" / "jules"
APP_DIR = JULES_CHECKOUT / "rose-stem" / "app"

pytestmark = pytest.mark.skipif(
    not APP_DIR.is_dir(), reason="needs the reference/jules sparse checkout"
)


def app_configs() -> list[Path]:
    """Every `rose-app.conf` in the checkout, in a stable order."""
    return sorted(APP_DIR.glob("*/rose-app.conf"))


def convert(path: Path) -> dict[str, str] | None:
    """Convert one app, or return `None` if it is not a JULES runtime app.

    Four of the upstream apps drive the build and the metadata linters rather
    than the model. They are recognised by shape, not by name: they either
    declare a `source=` token julesconf refuses (`git:`, or a bare
    `$VAR`-rooted path) or they target no `.nml` file at all. Both tests are
    properties of what the app *is*, so an upstream rename or a new build app
    needs no change here.
    """
    try:
        files = rose_to_namelists(RoseApp.parse_file(path), env={})
    except UnsupportedSourceError:
        return None
    if not any(name.endswith(".nml") for name in files):
        return None
    return files


def sweep() -> tuple[list[str], list[str], dict[str, str]]:
    """Run every app through the converter and the schemas.

    Returns:
        `(validated, skipped, failures)`, where `failures` maps an app name
        to its first validation error rendered as `location: message`.
    """
    validated, skipped, failures = [], [], {}
    for path in app_configs():
        name = path.parent.name
        files = convert(path)
        if files is None:
            skipped.append(name)
            continue
        data = {
            filename.removesuffix(".nml"): namelist_to_dict(f90nml.reads(text))
            for filename, text in files.items()
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                JulesNamelists.model_validate(data)
            except pydantic.ValidationError as exc:
                first = exc.errors()[0]
                location = ".".join(str(part) for part in first["loc"]) or "<config>"
                failures[name] = (
                    f"{location}: {first['msg']} "
                    f"[input={first.get('input')!r}] "
                    f"(+{exc.error_count() - 1} more)"
                )
                continue
        validated.append(name)
    return validated, skipped, failures


@pytest.fixture(scope="module")
def swept():
    """The whole sweep, run once."""
    return sweep()


class TestFullSweep:
    def test_the_checkout_holds_apps(self):
        """Guard against a sparse checkout that silently fetched nothing."""
        assert len(app_configs()) > 10

    def test_every_jules_app_validates(self, swept):
        validated, _, failures = swept
        assert not failures, "apps that do not validate:\n" + "\n".join(
            f"  {name}: {reason}" for name, reason in sorted(failures.items())
        )
        assert validated

    def test_non_jules_apps_are_skipped_not_failed(self, swept):
        """The build and linter apps must be recognised, not silently pass."""
        _, skipped, _ = swept
        assert skipped
        for name in skipped:
            files = None
            with contextlib.suppress(UnsupportedSourceError):
                files = rose_to_namelists(
                    RoseApp.parse_file(APP_DIR / name / "rose-app.conf"), env={}
                )
            assert files is None or not any(f.endswith(".nml") for f in files)

    def test_the_vendored_corpus_is_a_subset(self, swept):
        """Every vendored app must still exist upstream under the same name."""
        from .test_convert import APPS

        validated, _, _ = swept
        assert set(APPS) <= set(validated)
