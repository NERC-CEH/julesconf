"""Integration test: validate a minimal synthetic JulesNamelists.

Constructs a minimal valid JulesNamelists programmatically and verifies
it passes validation. This tests that the full model tree (all 29
namelists, cross-namelist checks) accepts a valid configuration.

Cross-namelist length validation is tested in test_cross_namelist.py.
"""

import pytest

from julesconf.schemas import JulesNamelists


def _minimal_valid() -> dict:
    return {
        "drive": {"jules_drive": {}},
        "initial_conditions": {"jules_initial": {}},
        "jules_hydrology": {"jules_hydrology": {}},
        "jules_radiation": {"jules_radiation": {}},
        "jules_soil": {"jules_soil": {}},
        "jules_surface": {"jules_surface": {}},
        "jules_surface_types": {"jules_surface_types": {"npft": 5, "nnvg": 4}},
        "jules_vegetation": {"jules_vegetation": {}},
        "model_environment": {"jules_model_environment": {}},
        "nveg_params": {"jules_nvegparm": {}},
        "pft_params": {"jules_pftparm": {}},
        "timesteps": {
            "jules_time": {
                "timestep_len": 1800,
                "main_run_start": "1997-01-01 00:00:00",
                "main_run_end": "1997-12-31 23:30:00",
            }
        },
    }


@pytest.fixture(scope="module")
def minimal_config() -> dict:
    return _minimal_valid()


def test_minimal_valid_config(minimal_config):
    """A minimal JulesNamelists should pass validation."""
    JulesNamelists.model_validate(minimal_config)


def test_minimal_values(minimal_config):
    """Values we set should be accessible through the model tree."""
    m = JulesNamelists.model_validate(minimal_config)
    assert m.jules_surface_types.jules_surface_types.npft == 5
    assert m.jules_surface_types.jules_surface_types.nnvg == 4
    assert m.timesteps.jules_time.timestep_len == 1800
