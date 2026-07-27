"""Gates for the advisory `warn-if` severity.

The rose metadata's third severity. Unlike every other julesconf warning, a
`DiscouragedValueWarning` does not mean anything was dropped or ignored — the
value takes effect exactly as written and upstream simply advises against it.
So the gates here are as much about *not* firing as about firing: a warning on
a default configuration would be noise, and noise is what gets filtered.
"""

import warnings

import pytest

from julesconf.schemas import JulesNamelists
from julesconf.schemas._conditional import DiscouragedValueWarning
from julesconf.schemas.imogen import ImogenAnlgValsList
from julesconf.schemas.jules_soil_biogeochem import Ch4Substrate, JulesSoilBiogeochem
from julesconf.schemas.jules_vegetation import CanModel, JulesVegetation


def test_deprecated_can_model_warns():
    """`can_model = 3` is deprecated upstream in favour of 4."""
    with pytest.warns(DiscouragedValueWarning, match="deprecated"):
        JulesVegetation(can_model=CanModel.radiative_heat_capacity)


def test_preferred_can_model_is_silent():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        JulesVegetation(can_model=CanModel.radiative_snow)


def test_microbe_scheme_warns_on_untuned_substrate():
    """The microbial methane scheme is only tuned for soil carbon."""
    with pytest.warns(DiscouragedValueWarning, match="only tuned"):
        JulesSoilBiogeochem(l_ch4_microbe=True, ch4_substrate=Ch4Substrate.npp)


def test_microbe_scheme_silent_on_soil_carbon():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        JulesSoilBiogeochem(l_ch4_microbe=True, ch4_substrate=Ch4Substrate.soil_carbon)


def test_substrate_alone_does_not_warn():
    """The rule is about the scheme, not the substrate.

    `ch4_substrate = npp` is an ordinary choice; it only becomes questionable
    once `l_ch4_microbe` selects the scheme that was not tuned for it.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        JulesSoilBiogeochem(ch4_substrate=Ch4Substrate.npp)


def test_zero_diffuse_fraction_warns():
    with pytest.warns(DiscouragedValueWarning, match="no diffuse downward SW"):
        ImogenAnlgValsList(diff_frac_const_imogen=0)


def test_nonzero_diffuse_fraction_is_silent():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        ImogenAnlgValsList(diff_frac_const_imogen=0.4)


@pytest.mark.parametrize(
    "model",
    [ImogenAnlgValsList, JulesSoilBiogeochem, JulesVegetation],
)
def test_defaults_are_never_discouraged(model):
    """A default-constructed block must not warn.

    julesconf writes every default explicitly, so a warning that fires on the
    defaults would fire on every config that has been round-tripped through
    `to_namelists` — which is exactly how a warning category gets globally
    filtered and stops being read.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        model()


def test_warning_is_independently_escalatable():
    """It must not be caught by a filter aimed at the other categories."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        warnings.simplefilter("error", DiscouragedValueWarning)
        with pytest.raises(DiscouragedValueWarning):
            JulesVegetation(can_model=CanModel.radiative_heat_capacity)


def _standalone():
    """Return a minimal valid standalone config, built the way conftest does."""
    from conftest import minimal_valid

    return minimal_valid()


def test_temp_fix_disabled_in_standalone_warns(tmp_path, monkeypatch):
    """Turning a standalone fix back off is visible, but not fatal."""
    monkeypatch.chdir(tmp_path)
    data = _standalone()
    data.setdefault("science_fixes", {}).setdefault("jules_temp_fixes", {})[
        "l_dtcanfix"
    ] = False
    with pytest.warns(DiscouragedValueWarning, match="l_dtcanfix should be .true."):
        JulesNamelists.model_validate(data)


def test_temp_fixes_defaults_do_not_warn(tmp_path, monkeypatch):
    """The shipped defaults already satisfy all seven rules."""
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DiscouragedValueWarning)
        JulesNamelists.model_validate(_standalone())


def test_temp_fixes_not_checked_outside_standalone(tmp_path, monkeypatch):
    """The rules are conditioned on l_jules_parent = standalone.

    A coupled configuration has a legitimate reason to reproduce historical
    behaviour, and upstream scopes every one of these rules to standalone.
    """
    monkeypatch.chdir(tmp_path)
    data = _standalone()
    data.setdefault("science_fixes", {}).setdefault("jules_temp_fixes", {})[
        "l_dtcanfix"
    ] = False
    data.setdefault("model_environment", {}).setdefault("jules_model_environment", {})[
        "l_jules_parent"
    ] = "um"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        warnings.simplefilter("error", DiscouragedValueWarning)
        JulesNamelists.model_validate(data)
