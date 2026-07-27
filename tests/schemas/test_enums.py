"""Tests for IntEnum name-or-value coercion and name_or_value utility."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.imogen import ChangeMetdataMethod, ImogenRunList
from julesconf.schemas.jules_deposition import (
    DepH2SoilScheme,
    DryDepModel,
    JulesDeposition,
)
from julesconf.schemas.jules_irrig import IrrCrop, JulesIrrig
from julesconf.schemas.jules_rivers import JulesRivers, RiverRoutingAlgorithm
from julesconf.schemas.jules_soil import JulesSoil, SoilhcMethod
from julesconf.schemas.jules_soil_biogeochem import (
    Ch4Substrate,
    JulesSoilBiogeochem,
    SoilBgcModel,
)
from julesconf.schemas.jules_surface import (
    FdHillOption,
    FdStabilityDep,
    FormDrag,
    IModiscOpt,
    JulesSurface,
    SrfExCnvGust,
)
from julesconf.schemas.jules_vegetation import (
    CanModel,
    JulesVegetation,
    PhotoAcclimModel,
    PhotoActModel,
    PhotoJvModel,
)
from julesconf.schemas.model_environment import (
    JulesModelEnvironment,
    JulesParent,
    LsmId,
)

# ---------------------------------------------------------------------------
# Model-level integration tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_cls", "field_name", "enum_cls", "valid_values"),
    [
        (JulesSoil, "soilhc_method", SoilhcMethod, [1, "johansen"]),
        (JulesRivers, "i_river_vn", RiverRoutingAlgorithm, [2, "rfm"]),
        (JulesIrrig, "irr_crop", IrrCrop, [0, "year_round"]),
        (
            JulesSoilBiogeochem,
            "soil_bgc_model",
            SoilBgcModel,
            [1, "single_pool"],
        ),
        (
            JulesSoilBiogeochem,
            "ch4_substrate",
            Ch4Substrate,
            [3, "soil_respiration"],
        ),
        (JulesVegetation, "can_model", CanModel, [4, "radiative_snow"]),
        (JulesModelEnvironment, "l_jules_parent", JulesParent, [0, "standalone"]),
        (JulesModelEnvironment, "lsm_id", LsmId, [1, "jules"]),
        (
            ImogenRunList,
            "change_metdata_method",
            ChangeMetdataMethod,
            [1, "analogue_patterns"],
        ),
        (
            JulesVegetation,
            "photo_acclim_model",
            PhotoAcclimModel,
            [0, "no_acclimation"],
        ),
        (JulesVegetation, "photo_act_model", PhotoActModel, [1, "vary_by_pft"]),
        (JulesVegetation, "photo_jv_model", PhotoJvModel, [1, "jmax_only"]),
        (JulesSurface, "formdrag", FormDrag, [0, "no_orographic_stress"]),
        (JulesSurface, "fd_hill_option", FdHillOption, [0, "steep_hill"]),
        (JulesSurface, "fd_stability_dep", FdStabilityDep, [0, "off"]),
        (JulesSurface, "i_modiscopt", IModiscOpt, [0, "off"]),
        (JulesSurface, "srf_ex_cnv_gust", SrfExCnvGust, [0, "off"]),
        (JulesDeposition, "dry_dep_model", DryDepModel, [1, "restricted_ukca"]),
        (
            JulesDeposition,
            "dep_h2_soil_scheme",
            DepH2SoilScheme,
            [1, "conrad_seiler"],
        ),
    ],
)
def test_enum_field_accepts_int_and_name(model_cls, field_name, enum_cls, valid_values):
    for val in valid_values:
        data = {field_name: val}
        m = model_cls.model_validate(data)
        assert getattr(m, field_name) == valid_values[0]  # first is the int value


@pytest.mark.parametrize(
    ("model_cls", "field_name", "invalid_value"),
    [
        (JulesSoil, "soilhc_method", "bad_name"),
        (JulesRivers, "i_river_vn", 99),
        (JulesIrrig, "irr_crop", "not_a_crop"),
        (JulesModelEnvironment, "l_jules_parent", "unknown"),
        (ImogenRunList, "change_metdata_method", 4),
    ],
)
def test_enum_field_rejects_invalid_value(model_cls, field_name, invalid_value):
    with pytest.raises(ValidationError, match=field_name):
        model_cls.model_validate({field_name: invalid_value})
