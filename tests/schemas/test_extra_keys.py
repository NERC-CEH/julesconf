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


def _output_with_repeated_blocks(n: int) -> dict:
    """Return an `output.nml` dict as `f90nml` renders `n` repeated groups.

    `jules_output` is deliberately the group repeated here, not
    `jules_output_profile`: the profile group *is* modelled as a list of
    blocks, so repeating it is representable and must not warn. This warning is
    now only about the rest -- a group julesconf holds one of.
    """
    return {
        **{f"_grp_jules_output_{i}": {"run_id": f"r{i}"} for i in range(n)},
        "jules_output_profile": [],
    }


def test_repeated_group_warns_once_naming_the_group_and_the_count():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate(_output_with_repeated_blocks(3))

    repeated = [x for x in w if issubclass(x.category, RepeatedNamelistGroupWarning)]
    assert len(repeated) == 1
    assert "jules_output" in str(repeated[0].message)
    assert "3 times" in str(repeated[0].message)


def test_repeated_group_does_not_also_warn_as_an_unknown_key():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate(_output_with_repeated_blocks(2))

    assert not any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)


def test_repeated_group_escalates_to_an_error():
    with warnings.catch_warnings():
        warnings.simplefilter("error", RepeatedNamelistGroupWarning)
        with pytest.raises(RepeatedNamelistGroupWarning, match="jules_output"):
            OutputNamelist.model_validate(_output_with_repeated_blocks(2))


def test_a_group_named_once_is_not_treated_as_repeated():
    """`_grp_` is only meaningful with the trailing index `f90nml` appends."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate({"_grp_jules_output": {}})

    assert not any(issubclass(x.category, RepeatedNamelistGroupWarning) for x in w)
    assert any(issubclass(x.category, UnknownNamelistKeyWarning) for x in w)


def test_a_modelled_repeated_group_does_not_warn():
    """The three groups JULES repeats are read as lists, and are not a gap."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        OutputNamelist.model_validate(
            {
                "jules_output": {"nprofiles": 2},
                "jules_output_profile": [{"profile_name": "a"}, {"profile_name": "b"}],
            }
        )

    assert not any(issubclass(x.category, RepeatedNamelistGroupWarning) for x in w)


def test_strict_from_namelists_rejects_a_repeated_group(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    JulesNamelists.model_validate(minimal_valid()).to_namelists(tmp_path)
    (tmp_path / "output.nml").write_text(
        "&jules_output\nrun_id='a',\n/\n&jules_output\nrun_id='b',\n/\n"
    )

    with pytest.raises(RepeatedNamelistGroupWarning, match="jules_output"):
        JulesNamelists.from_namelists(tmp_path, strict=True)
