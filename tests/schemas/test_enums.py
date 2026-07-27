"""Tests for IntEnum name-or-value coercion and name_or_value utility."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.imogen import ChangeMetdataMethod, ImogenRunList
from julesconf.schemas.jules_irrig import IrrCrop, JulesIrrig
from julesconf.schemas.jules_rivers import JulesRivers, RiverRoutingAlgorithm
from julesconf.schemas.jules_soil import JulesSoil, SoilhcMethod
from julesconf.schemas.jules_soil_biogeochem import (
    Ch4Substrate,
    JulesSoilBiogeochem,
    SoilBgcModel,
)
from julesconf.schemas.jules_vegetation import CanModel, JulesVegetation
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
