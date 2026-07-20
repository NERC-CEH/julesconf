"""Tests for cross-namelist list-length validators in JulesNamelists."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.namelists import JulesNamelists


def _minimal_valid(npft: int = 5, nnvg: int = 4, ncpft: int = 0) -> dict:
    return {
        "drive": {"jules_drive": {}},
        "initial_conditions": {"jules_initial": {}},
        "jules_hydrology": {"jules_hydrology": {}},
        "jules_radiation": {"jules_radiation": {}},
        "jules_soil": {"jules_soil": {}},
        "jules_surface": {"jules_surface": {}},
        "jules_surface_types": {
            "jules_surface_types": {"npft": npft, "nnvg": nnvg, "ncpft": ncpft}
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


# ---------------------------------------------------------------------------
# Positive: correct lengths validate
# ---------------------------------------------------------------------------


def test_correct_lengths_validate():
    data = _minimal_valid(npft=3, nnvg=2, ncpft=1)
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1, 0.2, 0.3]}}
    data["pft_params"] = {"jules_pftparm": {"canht_ft_io": [1.0, 2.0, 3.0]}}
    data["nveg_params"] = {"jules_nvegparm": {"albsnc_nvg_io": [0.1, 0.2]}}
    data["crop_params"] = {
        "jules_cropparm": {
            "cfrac_s_io": [0.5, 0.5, 0.5],
            "t_bse_io": [273.15],
        }
    }
    data["jules_snow"] = {"jules_snow": {"cansnowpft": [True, False, True]}}
    data["jules_deposition"] = {"jules_deposition_species": {"rsurf_std_io": [1.0] * 5}}
    JulesNamelists.model_validate(data)


# ---------------------------------------------------------------------------
# Negative: wrong lengths raise
# ---------------------------------------------------------------------------


def test_triffid_wrong_npft():
    data = _minimal_valid()
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1, 0.2]}}
    with pytest.raises(
        ValidationError, match=r"triffid_params\.jules_triffid\.g_area_io"
    ):
        JulesNamelists.model_validate(data)


def test_pft_wrong_npft():
    data = _minimal_valid()
    data["pft_params"] = {"jules_pftparm": {"canht_ft_io": [1.0] * 4}}
    with pytest.raises(
        ValidationError, match=r"pft_params\.jules_pftparm\.canht_ft_io"
    ):
        JulesNamelists.model_validate(data)


def test_nveg_wrong_nnvg():
    data = _minimal_valid()
    data["nveg_params"] = {"jules_nvegparm": {"albsnc_nvg_io": [0.1] * 3}}
    with pytest.raises(
        ValidationError, match=r"nveg_params\.jules_nvegparm\.albsnc_nvg_io"
    ):
        JulesNamelists.model_validate(data)


def test_crop_ncpft_wrong():
    data = _minimal_valid(ncpft=2)
    data["crop_params"] = {"jules_cropparm": {"t_bse_io": [273.15] * 3}}
    with pytest.raises(ValidationError, match=r"crop_params\.jules_cropparm\.t_bse_io"):
        JulesNamelists.model_validate(data)


def test_crop_cfrac_s_io_wrong_npft():
    data = _minimal_valid()
    data["crop_params"] = {"jules_cropparm": {"cfrac_s_io": [0.5] * 4}}
    with pytest.raises(
        ValidationError, match=r"crop_params\.jules_cropparm\.cfrac_s_io"
    ):
        JulesNamelists.model_validate(data)


def test_snow_npft_wrong():
    data = _minimal_valid()
    data["jules_snow"] = {"jules_snow": {"cansnowpft": [True] * 4}}
    with pytest.raises(ValidationError, match=r"jules_snow\.jules_snow\.cansnowpft"):
        JulesNamelists.model_validate(data)


def test_deposition_ntype_wrong():
    data = _minimal_valid()
    data["jules_deposition"] = {"jules_deposition_species": {"rsurf_std_io": [1.0] * 8}}
    with pytest.raises(
        ValidationError,
        match=r"jules_deposition\.jules_deposition_species\.rsurf_std_io",
    ):
        JulesNamelists.model_validate(data)
