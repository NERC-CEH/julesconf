"""Tests for julesconf.schemas.timesteps."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.timesteps import JulesSpinup, JulesTime, TimestepsNamelist

# ---------------------------------------------------------------------------
# Fixtures / shared data
# ---------------------------------------------------------------------------

VALID_JULES_TIME = {
    "timestep_len": 3600,
    "main_run_start": "1997-01-01 00:00:00",
    "main_run_end": "1998-01-01 00:00:00",
}

VALID_JULES_SPINUP_NO_SPINUP = {
    "max_spinup_cycles": 0,
}

VALID_JULES_SPINUP_WITH_VARS = {
    "max_spinup_cycles": 5,
    "spinup_start": "1996-01-01 00:00:00",
    "spinup_end": "1997-01-01 00:00:00",
    "nvars": 2,
    "var": ["smcl", "t_soil"],
    "use_percent": [False, True],
    "tolerance": [1.0, 0.1],
}


# ---------------------------------------------------------------------------
# JulesTime
# ---------------------------------------------------------------------------


def test_jules_time_valid_minimal():
    JulesTime.model_validate(VALID_JULES_TIME)


def test_jules_time_defaults():
    m = JulesTime.model_validate(VALID_JULES_TIME)
    assert m.l_360 is False
    assert m.l_leap is True
    assert m.l_local_solar_time is False
    assert m.print_step == 1


def test_jules_time_extra_fields_ignored():
    data = {**VALID_JULES_TIME, "unknown_field": 99}
    JulesTime.model_validate(data)


@pytest.mark.parametrize("timestep_len", [0, -1, -3600])
def test_jules_time_timestep_len_invalid(timestep_len):
    data = {**VALID_JULES_TIME, "timestep_len": timestep_len}
    with pytest.raises(ValidationError, match="timestep_len"):
        JulesTime.model_validate(data)


@pytest.mark.parametrize("print_step", [0, -1])
def test_jules_time_print_step_invalid(print_step):
    data = {**VALID_JULES_TIME, "print_step": print_step}
    with pytest.raises(ValidationError, match="print_step"):
        JulesTime.model_validate(data)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("main_run_start", "01-01-1997 00:00:00"),
        ("main_run_start", "1997/01/01 00:00:00"),
        ("main_run_start", "1997-01-01"),
        ("main_run_end", "not-a-date"),
    ],
)
def test_jules_time_datetime_format_invalid(field, bad_value):
    data = {**VALID_JULES_TIME, field: bad_value}
    with pytest.raises(ValidationError, match=field):
        JulesTime.model_validate(data)


# ---------------------------------------------------------------------------
# JulesSpinup
# ---------------------------------------------------------------------------


def test_jules_spinup_defaults():
    m = JulesSpinup.model_validate({})
    assert m.max_spinup_cycles == 0
    assert m.nvars == 0
    assert m.var is None
    assert m.tolerance is None
    assert m.use_percent is None


def test_jules_spinup_valid_no_spinup():
    JulesSpinup.model_validate(VALID_JULES_SPINUP_NO_SPINUP)


def test_jules_spinup_valid_with_vars():
    JulesSpinup.model_validate(VALID_JULES_SPINUP_WITH_VARS)


def test_jules_spinup_use_percent_optional_when_nvars_gt0():
    data = {**VALID_JULES_SPINUP_WITH_VARS}
    del data["use_percent"]
    JulesSpinup.model_validate(data)


@pytest.mark.parametrize("max_spinup_cycles", [-1, -5])
def test_jules_spinup_max_cycles_negative(max_spinup_cycles):
    with pytest.raises(ValidationError, match="max_spinup_cycles"):
        JulesSpinup.model_validate({"max_spinup_cycles": max_spinup_cycles})


def test_jules_spinup_missing_spinup_start():
    data = {**VALID_JULES_SPINUP_WITH_VARS}
    del data["spinup_start"]
    with pytest.raises(ValidationError, match="spinup_start"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_missing_spinup_end():
    data = {**VALID_JULES_SPINUP_WITH_VARS}
    del data["spinup_end"]
    with pytest.raises(ValidationError, match="spinup_end"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_missing_var_when_nvars_gt0():
    data = {**VALID_JULES_SPINUP_WITH_VARS}
    del data["var"]
    with pytest.raises(ValidationError, match="var"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_missing_tolerance_when_nvars_gt0():
    data = {**VALID_JULES_SPINUP_WITH_VARS}
    del data["tolerance"]
    with pytest.raises(ValidationError, match="tolerance"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_var_length_mismatch():
    data = {**VALID_JULES_SPINUP_WITH_VARS, "var": ["smcl", "t_soil", "c_veg"]}
    with pytest.raises(ValidationError, match="var"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_tolerance_length_mismatch():
    data = {**VALID_JULES_SPINUP_WITH_VARS, "tolerance": [1.0]}
    with pytest.raises(ValidationError, match="tolerance"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_use_percent_length_mismatch():
    data = {**VALID_JULES_SPINUP_WITH_VARS, "use_percent": [False]}
    with pytest.raises(ValidationError, match="use_percent"):
        JulesSpinup.model_validate(data)


def test_jules_spinup_invalid_var_value():
    data = {**VALID_JULES_SPINUP_WITH_VARS, "var": ["smcl", "unknown_var"]}
    with pytest.raises(ValidationError, match="var"):
        JulesSpinup.model_validate(data)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("spinup_start", "01-01-1996 00:00:00"),
        ("spinup_end", "not-a-date"),
    ],
)
def test_jules_spinup_datetime_format_invalid(field, bad_value):
    data = {**VALID_JULES_SPINUP_WITH_VARS, field: bad_value}
    with pytest.raises(ValidationError, match=field):
        JulesSpinup.model_validate(data)


# ---------------------------------------------------------------------------
# TimestepsNamelist
# ---------------------------------------------------------------------------


def test_timesteps_namelist_valid_no_spinup():
    TimestepsNamelist.model_validate(
        {
            "jules_time": VALID_JULES_TIME,
            "jules_spinup": VALID_JULES_SPINUP_NO_SPINUP,
        }
    )


def test_timesteps_namelist_valid_with_spinup():
    TimestepsNamelist.model_validate(
        {
            "jules_time": VALID_JULES_TIME,
            "jules_spinup": VALID_JULES_SPINUP_WITH_VARS,
        }
    )


def test_timesteps_namelist_jules_spinup_optional():
    TimestepsNamelist.model_validate({"jules_time": VALID_JULES_TIME})


def test_timesteps_namelist_missing_jules_time():
    with pytest.raises(ValidationError, match="jules_time"):
        TimestepsNamelist.model_validate({"jules_spinup": VALID_JULES_SPINUP_NO_SPINUP})
