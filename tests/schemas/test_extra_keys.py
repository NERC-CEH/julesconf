"""Tests for unknown-key warning behaviour on NamelistModel."""

import warnings

import pytest
from conftest import minimal_valid

from julesconf.schemas import JulesNamelists
from julesconf.schemas._base import (
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
)
from julesconf.schemas.output import OutputNamelist
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


# ---------------------------------------------------------------------------
# Repeated namelist groups
# ---------------------------------------------------------------------------


def _output_with_repeated_profiles(n: int) -> dict:
    """Return an `output.nml` dict as `f90nml` renders `n` repeated groups."""
    return {
        "jules_output": {"run_id": "test", "output_dir": "./output"},
        **{
            f"_grp_jules_output_profile_{i}": {"profile_name": f"p{i}"}
            for i in range(n)
        },
    }


def test_repeated_group_warns_once_naming_the_group_and_the_count():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate(_output_with_repeated_profiles(3))

    repeated = [x for x in w if issubclass(x.category, RepeatedNamelistGroupWarning)]
    assert len(repeated) == 1
    assert "jules_output_profile" in str(repeated[0].message)
    assert "3 times" in str(repeated[0].message)


def test_repeated_group_does_not_also_warn_as_an_unknown_key():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate(_output_with_repeated_profiles(2))

    assert not any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)


def test_repeated_group_escalates_to_an_error():
    with warnings.catch_warnings():
        warnings.simplefilter("error", RepeatedNamelistGroupWarning)
        with pytest.raises(RepeatedNamelistGroupWarning, match="jules_output_profile"):
            OutputNamelist.model_validate(_output_with_repeated_profiles(2))


def test_a_group_named_once_is_not_treated_as_repeated():
    """`_grp_` is only meaningful with the trailing index `f90nml` appends."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate({"_grp_jules_output_profile": {}})

    assert not any(issubclass(x.category, RepeatedNamelistGroupWarning) for x in w)
    assert any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)


def test_strict_from_namelists_rejects_a_repeated_group(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    JulesNamelists.model_validate(minimal_valid()).to_namelists(tmp_path)
    (tmp_path / "output.nml").write_text(
        "&jules_output\nrun_id='test',\noutput_dir='./output',\n/\n"
        "&jules_output_profile\nprofile_name='a',\n/\n"
        "&jules_output_profile\nprofile_name='b',\n/\n"
    )

    with pytest.raises(RepeatedNamelistGroupWarning, match="jules_output_profile"):
        JulesNamelists.from_namelists(tmp_path, strict=True)
