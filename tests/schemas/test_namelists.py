"""Integration test: validate the loobos example namelists.

Reads the loobos namelists directory using NamelistConfig, then validates
the resulting dict with JulesNamelists.  Any validation failure is a real
signal: either the loobos config is misconfigured, or the schema has an
incorrect constraint.
"""

from pathlib import Path

import pytest

from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists

LOOBOS_NAMELISTS = Path(__file__).parents[1] / "data" / "loobos" / "namelists"


@pytest.fixture(scope="module")
def loobos_data() -> dict:
    return NamelistConfig().read(LOOBOS_NAMELISTS)


def test_loobos_namelists_validate(loobos_data):
    """The full loobos namelists directory should pass validation."""
    JulesNamelists.model_validate(loobos_data)


def test_loobos_npft(loobos_data):
    m = JulesNamelists.model_validate(loobos_data)
    assert m.jules_surface_types.jules_surface_types.npft == 5


def test_loobos_nnvg(loobos_data):
    m = JulesNamelists.model_validate(loobos_data)
    assert m.jules_surface_types.jules_surface_types.nnvg == 4


def test_loobos_sm_levels(loobos_data):
    m = JulesNamelists.model_validate(loobos_data)
    assert m.jules_soil.jules_soil.sm_levels == 4


def test_loobos_timestep_len(loobos_data):
    m = JulesNamelists.model_validate(loobos_data)
    assert m.timesteps.jules_time.timestep_len == 1800
