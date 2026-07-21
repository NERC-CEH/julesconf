"""Tests for cross-namelist list-length validators in JulesNamelists."""

import pytest
from pydantic import ValidationError

from julesconf.schemas import JulesNamelists
from julesconf.schemas._base import NamelistModel
from julesconf.schemas._namelists import find_list_len
from julesconf.schemas.constraints import ListLen


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


# ---------------------------------------------------------------------------
# Regression: fields that spelled the annotation as
# `Annotated[list[X], ListLen(...)] | None`, hiding the marker from the
# length check inside a union member so it silently never ran.
# ---------------------------------------------------------------------------


def test_pft_lai_alb_lim_wrong_npft():
    data = _minimal_valid()
    data["pft_params"] = {"jules_pftparm": {"lai_alb_lim_io": [1.0] * 4}}
    with pytest.raises(
        ValidationError, match=r"pft_params\.jules_pftparm\.lai_alb_lim_io"
    ):
        JulesNamelists.model_validate(data)


def test_pft_z0hm_classic_wrong_npft():
    data = _minimal_valid()
    data["pft_params"] = {"jules_pftparm": {"z0hm_classic_pft_io": [1.0] * 4}}
    with pytest.raises(
        ValidationError, match=r"pft_params\.jules_pftparm\.z0hm_classic_pft_io"
    ):
        JulesNamelists.model_validate(data)


def test_nveg_z0hm_classic_wrong_nnvg():
    data = _minimal_valid()
    data["nveg_params"] = {"jules_nvegparm": {"z0hm_classic_nvg_io": [1.0] * 3}}
    with pytest.raises(
        ValidationError, match=r"nveg_params\.jules_nvegparm\.z0hm_classic_nvg_io"
    ):
        JulesNamelists.model_validate(data)


# ---------------------------------------------------------------------------
# Meta: every ListLen in the model tree must be reachable by the length check
# ---------------------------------------------------------------------------


def _walk_fields(model: type[NamelistModel], path: str = ""):
    """Yield `(dotted_path, field_info)` for every field in the model tree."""
    for name, field_info in model.model_fields.items():
        field_path = f"{path}.{name}" if path else name
        annotation = field_info.annotation
        if isinstance(annotation, type) and issubclass(annotation, NamelistModel):
            yield from _walk_fields(annotation, field_path)
        else:
            yield field_path, field_info


def test_every_list_len_uses_canonical_spelling():
    """Every ListLen must sit on the outermost `Annotated`.

    `find_list_len` tolerates `Annotated[list[X], ListLen(...)] | None`, but
    that spelling hides the marker from `FieldInfo.metadata` and previously
    disabled the length check silently. Keep one spelling across the schemas:
    `Annotated[list[X] | None, ListLen(...)]`.
    """
    non_canonical = [
        path
        for path, field_info in _walk_fields(JulesNamelists)
        if find_list_len(field_info) is not None
        and not any(isinstance(m, ListLen) for m in field_info.metadata)
    ]
    assert non_canonical == []


# ---------------------------------------------------------------------------
# nnpft: TRIFFID arrays are declared real(npft) but only nnpft values are read
# ---------------------------------------------------------------------------


def test_triffid_accepts_nnpft_length():
    """The canonical length: one value per natural PFT."""
    data = _minimal_valid(npft=5, nnvg=4, ncpft=2)  # nnpft = 3
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1, 0.2, 0.3]}}
    JulesNamelists.model_validate(data)


def test_triffid_tolerates_npft_length():
    """The declared length: existing configs supply one value per PFT."""
    data = _minimal_valid(npft=5, nnvg=4, ncpft=2)
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1, 0.2, 0.3, 0.0, 0.0]}}
    JulesNamelists.model_validate(data)


def test_triffid_rejects_other_lengths():
    """A length that is neither nnpft nor npft is still an error."""
    data = _minimal_valid(npft=5, nnvg=4, ncpft=2)
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1, 0.2, 0.3, 0.4]}}
    with pytest.raises(ValidationError, match=r"expected nnpft=3 or npft=5"):
        JulesNamelists.model_validate(data)


def test_triffid_lengths_coincide_without_crops():
    """With ncpft = 0 the two accepted lengths are the same."""
    data = _minimal_valid(npft=5, nnvg=4, ncpft=0)
    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1] * 5}}
    JulesNamelists.model_validate(data)

    data["triffid_params"] = {"jules_triffid": {"g_area_io": [0.1] * 4}}
    with pytest.raises(ValidationError, match=r"g_area_io"):
        JulesNamelists.model_validate(data)


def test_tolerated_length_is_written_back_unchanged():
    """A tolerated npft-length array round-trips without being truncated."""
    data = _minimal_valid(npft=5, nnvg=4, ncpft=2)
    supplied = [0.1, 0.2, 0.3, 0.0, 0.0]
    data["triffid_params"] = {"jules_triffid": {"g_area_io": supplied}}

    written = JulesNamelists.model_validate(data).to_namelist_dict()
    assert written["triffid_params"]["jules_triffid"]["g_area_io"] == supplied


def test_list_len_rejects_unknown_tolerated_dim():
    """A typo in `tolerates` fails loudly, like a typo in `dim`."""
    with pytest.raises(ValueError, match="Unknown ListLen dim 'npfts'"):
        ListLen("nnpft", tolerates=("npfts",))
