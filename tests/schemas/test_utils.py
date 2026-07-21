"""Tests for the shared schema field utilities in ``julesconf.schemas._utils``."""

import pytest
from pydantic import ValidationError

from julesconf.schemas._utils import LIST_LEN_DIMS, ListLen
from julesconf.schemas.namelists import JulesNamelists
from julesconf.schemas.nveg_params import JulesNvegparm

# ---------------------------------------------------------------------------
# SentinelOrFraction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [-1.0, 0.0, 0.5, 1.0])
def test_sentinel_or_fraction_accepts(value):
    model = JulesNvegparm.model_validate({"albsnf_nvg_io": [value]})
    assert model.albsnf_nvg_io == [value]


@pytest.mark.parametrize("value", [-0.5, 1.5, -2.0])
def test_sentinel_or_fraction_rejects_out_of_range(value):
    with pytest.raises(ValidationError, match="sentinel"):
        JulesNvegparm.model_validate({"albsnf_nvg_io": [value]})


@pytest.mark.parametrize("value", ["oops", None, [], {}])
def test_sentinel_or_fraction_rejects_non_numeric(value):
    """Non-numeric input must be a ValidationError, not a raw TypeError.

    The range check previously ran before Pydantic's float coercion, so
    comparing e.g. a str against a float raised TypeError, which Pydantic does
    not convert into a validation error.
    """
    with pytest.raises(ValidationError):
        JulesNvegparm.model_validate({"albsnf_nvg_io": [value]})


def test_sentinel_or_fraction_coerces_int():
    model = JulesNvegparm.model_validate({"albsnf_nvg_io": [-1]})
    assert model.albsnf_nvg_io == [-1.0]


# ---------------------------------------------------------------------------
# ListLen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dim", sorted(LIST_LEN_DIMS))
def test_list_len_accepts_known_dims(dim):
    assert ListLen(dim).dim == dim


def test_list_len_rejects_unknown_dim():
    with pytest.raises(ValueError, match="Unknown ListLen dim 'bogus'"):
        ListLen("bogus")


def test_jules_namelists_resolves_every_dim():
    """The length check must supply a value for every dim ListLen permits."""
    data = {
        "drive": {"jules_drive": {}},
        "initial_conditions": {"jules_initial": {}},
        "jules_hydrology": {"jules_hydrology": {}},
        "jules_radiation": {"jules_radiation": {}},
        "jules_soil": {"jules_soil": {}},
        "jules_surface": {"jules_surface": {}},
        "jules_surface_types": {
            "jules_surface_types": {"npft": 5, "nnvg": 4, "ncpft": 0}
        },
        "jules_vegetation": {"jules_vegetation": {}},
        "model_environment": {"jules_model_environment": {}},
        "nveg_params": {"jules_nvegparm": {}},
        "pft_params": {"jules_pftparm": {}},
        "timesteps": {
            "jules_time": {
                "timestep_len": 1800,
                "main_run_start": "1997-01-01 00:00:00",
                "main_run_end": "1998-01-01 00:00:00",
            },
            "jules_spinup": {"max_spinup_cycles": 0},
        },
    }
    model = JulesNamelists.model_validate(data)
    surface_types = model.jules_surface_types.jules_surface_types
    dims = {
        "npft": surface_types.npft,
        "nnvg": surface_types.nnvg,
        "ncpft": surface_types.ncpft,
        "ntype": surface_types.npft + surface_types.nnvg,
    }
    assert set(dims) == set(LIST_LEN_DIMS)
