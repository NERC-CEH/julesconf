"""Tests for unknown-key warning behaviour on NamelistModel."""

import warnings

import pytest

from julesconf.schemas import JulesNamelists
from julesconf.schemas._base import UnknownNamelistKeyWarning
from julesconf.schemas.timesteps import JulesTime


def test_known_keys_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        JulesTime.model_validate(
            {
                "timestep_len": 1800,
                "main_run_start": "1997-01-01 00:00:00",
                "main_run_end": "1998-01-01 00:00:00",
            }
        )
        assert not any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)


def test_unknown_key_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        JulesTime.model_validate(
            {
                "timestep_len": 1800,
                "main_run_start": "1997-01-01 00:00:00",
                "main_run_end": "1998-01-01 00:00:00",
                "timestep_length": 3600,  # typo
            }
        )
        assert any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)
        assert any("timestep_length" in str(x.message) for x in w)


def test_escalate_warning_to_error():
    with warnings.catch_warnings():
        warnings.simplefilter("error", UnknownNamelistKeyWarning)
        with pytest.raises(UnknownNamelistKeyWarning, match="unknown_namelist_member"):
            JulesTime.model_validate(
                {
                    "timestep_len": 1800,
                    "main_run_start": "1997-01-01 00:00:00",
                    "main_run_end": "1998-01-01 00:00:00",
                    "unknown_namelist_member": 123,
                }
            )


def test_top_level_unknown_key_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        JulesNamelists.model_validate(
            {
                "jules_surface_types": {"jules_surface_types": {"npft": 1, "nnvg": 1}},
                "drive": {"jules_drive": {}},
                "initial_conditions": {"jules_initial": {}},
                "jules_hydrology": {"jules_hydrology": {}},
                "jules_radiation": {"jules_radiation": {}},
                "jules_soil": {"jules_soil": {}},
                "jules_surface": {"jules_surface": {}},
                "jules_vegetation": {"jules_vegetation": {}},
                "model_environment": {"jules_model_environment": {}},
                "nveg_params": {"jules_nvegparm": {}},
                "pft_params": {"jules_pftparm": {}},
                "timesteps": {
                    "jules_time": {
                        "timestep_len": 1800,
                        "main_run_start": "1997-01-01 00:00:00",
                        "main_run_end": "1998-01-01 00:00:00",
                    }
                },
                "unknown_top_level_key": {},
            }
        )
        assert any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)
