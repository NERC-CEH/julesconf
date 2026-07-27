"""Tests for IntEnum name-or-value coercion and name_or_value utility."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.drive import JulesDrive, PrecipDisaggMethod
from julesconf.schemas.imogen import ChangeMetdataMethod, ImogenRunList
from julesconf.schemas.jules_deposition import (
    DepH2SoilScheme,
    DryDepModel,
    JulesDeposition,
)
from julesconf.schemas.jules_irrig import IrrCrop, JulesIrrig
from julesconf.schemas.jules_radiation import JulesRadiation, SeaAlbedoMethod
from julesconf.schemas.jules_rivers import (
    JulesOverbank,
    JulesRivers,
    LakeWaterConserveMethod,
    OverbankModel,
    RiverRoutingAlgorithm,
    TripGlobeShape,
)
from julesconf.schemas.jules_snow import (
    BasalMeltingOpt,
    FracSnowSublMelt,
    GrainGrowthOpt,
    GraupelOptions,
    JulesSnow,
    RelayerOpt,
    SnowCondParm,
)
from julesconf.schemas.jules_soil import JulesSoil, SoilhcMethod
from julesconf.schemas.jules_soil_biogeochem import (
    Ch4Substrate,
    JulesSoilBiogeochem,
    SoilBgcModel,
)
from julesconf.schemas.jules_surface import (
    AggregateOpt,
    AllTiles,
    AnthropHeatOption,
    FdHillOption,
    FdStabilityDep,
    FormDrag,
    IModiscOpt,
    JulesSurface,
    MoIterCorrection,
    ScreenDiagMethod,
    SrfExCnvGust,
)
from julesconf.schemas.jules_vegetation import (
    CanModel,
    FsmcShape,
    JulesVegetation,
    PhotoAcclimModel,
    PhotoActModel,
    PhotoJvModel,
)
from julesconf.schemas.jules_water_resources import (
    JulesWaterResources,
    NrGwaterModel,
)
from julesconf.schemas.model_environment import (
    JulesModelEnvironment,
    JulesParent,
    LsmId,
)
from julesconf.schemas.output import FilePeriod, JulesOutputProfile
from julesconf.schemas.science_fixes import CtileOrogFix, JulesTempFixes

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
        # Phase 2a
        (
            JulesDrive,
            "precip_disagg_method",
            PrecipDisaggMethod,
            [4, "random_wet_dry"],
        ),
        (JulesRadiation, "i_sea_alb_method", SeaAlbedoMethod, [3, "jin"]),
        (JulesSurface, "iscrntdiag", ScreenDiagMethod, [2, "transient"]),
        (
            JulesSurface,
            "cor_mo_iter",
            MoIterCorrection,
            [4, "improve_initial_guess"],
        ),
        (
            JulesSurface,
            "i_aggregate_opt",
            AggregateOpt,
            [1, "separate_aggregation"],
        ),
        (JulesVegetation, "fsmc_shape", FsmcShape, [1, "linear_pot"]),
        (JulesSnow, "graupel_options", GraupelOptions, [2, "treat_separately"]),
        (JulesSnow, "i_snow_cond_parm", SnowCondParm, [1, "calonne2011"]),
        (
            JulesSnow,
            "i_grain_growth_opt",
            GrainGrowthOpt,
            [1, "taillandier2007_et"],
        ),
        (JulesSnow, "i_relayer_opt", RelayerOpt, [1, "inverse_grain_size"]),
        (
            JulesSnow,
            "i_basal_melting_opt",
            BasalMeltingOpt,
            [1, "instantaneous"],
        ),
        (JulesOverbank, "overbank_model", OverbankModel, [3, "hypsometric"]),
        (
            JulesRivers,
            "lake_water_conserve_method",
            LakeWaterConserveMethod,
            [2, "elake_surft"],
        ),
        (JulesRivers, "trip_globe_shape", TripGlobeShape, [1, "spherical"]),
        (
            JulesWaterResources,
            "nr_gwater_model",
            NrGwaterModel,
            [1, "last_resort"],
        ),
        (
            JulesTempFixes,
            "ctile_orog_fix",
            CtileOrogFix,
            [1, "correct_sea_adjust_land"],
        ),
        (JulesOutputProfile, "file_period", FilePeriod, [-2, "annual"]),
        # Phase 2b — on/off switches kept as IntEnum, not bool
        (JulesSnow, "frac_snow_subl_melt", FracSnowSublMelt, [1, "on"]),
        (JulesSurface, "all_tiles", AllTiles, [1, "on"]),
        (JulesSurface, "anthrop_heat_option", AnthropHeatOption, [1, "flanner"]),
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
        (JulesDrive, "precip_disagg_method", 0),
        (JulesSurface, "iscrntdiag", 4),
        (JulesSnow, "graupel_options", "not_a_scheme"),
        (JulesOutputProfile, "file_period", -4),
        (JulesTempFixes, "ctile_orog_fix", 3),
    ],
)
def test_enum_field_rejects_invalid_value(model_cls, field_name, invalid_value):
    with pytest.raises(ValidationError, match=field_name):
        model_cls.model_validate({field_name: invalid_value})
