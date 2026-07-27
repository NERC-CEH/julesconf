"""Tests for the conditional (`fail-if` / `trigger`) rules from the rose metadata.

One test per implemented rule family. `fail-if` rules must raise; `trigger`
rules must emit `InactiveNamelistKeyWarning` and nothing stronger.

The rule ids each test covers are recorded in
`tests/data/rose_meta/rules_disposition.toml`; `test_rose_rule_coverage.py`
keeps that file honest against the extract.
"""

import warnings

import pytest
from conftest import minimal_valid
from pydantic import ValidationError

from julesconf.schemas import InactiveNamelistKeyWarning, JulesNamelists
from julesconf.schemas._conditional import is_specified
from julesconf.schemas.ancillaries import JulesRiversProps
from julesconf.schemas.imogen import ChangeMetdataMethod, ImogenRunList
from julesconf.schemas.jules_hydrology import JulesHydrology
from julesconf.schemas.jules_irrig import JulesIrrig
from julesconf.schemas.jules_radiation import JulesRadiation
from julesconf.schemas.jules_rivers import JulesRivers
from julesconf.schemas.jules_snow import JulesSnow
from julesconf.schemas.jules_soil import JulesSoil
from julesconf.schemas.jules_soil_biogeochem import (
    JulesSoilBiogeochem,
    SoilBgcModel,
)
from julesconf.schemas.jules_surface import JulesSurface
from julesconf.schemas.jules_surface_types import JulesSurfaceTypes
from julesconf.schemas.jules_vegetation import JulesVegetation
from julesconf.schemas.jules_water_resources import JulesWaterResources
from julesconf.schemas.model_environment import JulesModelEnvironment
from julesconf.schemas.urban import JulesUrban


def inactive(model_cls, **kwargs) -> list[str]:
    """Return the members reported inactive when building `model_cls`."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model_cls(**kwargs)
    return [
        str(record.message)
        for record in caught
        if issubclass(record.category, InactiveNamelistKeyWarning)
    ]


def build(**overrides) -> JulesNamelists:
    """Validate a minimal config with `{namelist: {block: {...}}}` overrides."""
    data = minimal_valid()
    for namelist, blocks in overrides.items():
        target = data.setdefault(namelist, {})
        for block, members in blocks.items():
            target.setdefault(block, {}).update(members)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return JulesNamelists.model_validate(data)


# --------------------------------------------------------------------------
# is_specified
# --------------------------------------------------------------------------


def test_is_specified_ignores_a_value_equal_to_the_default():
    """A round-tripped default must not look like a deliberate choice."""
    block = JulesSoilBiogeochem(kaps=JulesSoilBiogeochem.model_fields["kaps"].default)
    assert not is_specified(block, "kaps")
    assert is_specified(JulesSoilBiogeochem(kaps=1.0), "kaps")


def test_is_specified_is_false_for_an_unknown_member():
    assert not is_specified(JulesSoilBiogeochem(), "not_a_member")


# --------------------------------------------------------------------------
# fail-if, within a block
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_cls", "kwargs", "message"),
    [
        (
            JulesSoilBiogeochem,
            {"l_ch4_interactive": True, "l_ch4_tlayered": False},
            "l_ch4_tlayered",
        ),
        (JulesSoilBiogeochem, {"l_layeredc": True, "soil_bgc_model": 3}, "ecosse"),
        (
            JulesHydrology,
            {
                "l_top": True,
                "l_pdm": True,
                "zw_max": 6.0,
                "ti_max": 10.0,
                "ti_wetl": 1.5,
                "nfita": 20,
            },
            "TOPMODEL and PDM",
        ),
        (JulesHydrology, {"l_spdmvar": True, "l_pdm": False}, "l_spdmvar"),
        (
            JulesRadiation,
            {"l_snow_albedo": True, "l_spec_albedo": False},
            "l_spec_albedo=T",
        ),
        (
            JulesRadiation,
            {"l_embedded_snow": True, "l_spec_albedo": False},
            "l_spec_albedo must also be T",
        ),
        (
            JulesRadiation,
            {"l_embedded_snow": True, "l_spec_albedo": True, "l_snow_albedo": True},
            "exclusive of l_snow_albedo",
        ),
        (
            JulesIrrig,
            {"frac_irrig_all_tiles": True, "set_irrfrac_on_irrtiles": True},
            "cannot set both",
        ),
        (JulesSoil, {"dzsoil_elev": 0.0}, "positive value"),
        (JulesVegetation, {"l_trif_crop": True, "l_trif_eq": True}, "l_trif_crop"),
        (JulesVegetation, {"l_trif_fire": True, "l_trif_eq": True}, "l_trif_fire"),
        (JulesVegetation, {"l_trif_biocrop": True}, "l_trif_biocrop"),
        (JulesVegetation, {"l_croprotate": True}, "l_prescsow"),
        (
            JulesVegetation,
            {"stomata_model": 3, "l_scale_resp_pm": True, "can_rad_mod": 1},
            "l_scale_resp_pm",
        ),
        (JulesVegetation, {"stomata_model": 3, "can_rad_mod": 4}, "can_rad_mod"),
        (JulesUrban, {"l_urban_empirical": True}, "l_urban_empirical"),
        (JulesModelEnvironment, {"lsm_id": 2, "l_jules_parent": 1}, "CABLE"),
        (
            JulesRiversProps,
            {"coordinate_file": "rivers_%vv.nc"},
            "Coordinate file cannot contain variable name template",
        ),
        (
            JulesRiversProps,
            {"file": "rivers_%vv.nc"},
            "file to read coordinates from must be specified",
        ),
        (
            JulesRiversProps,
            {"read_list": True, "file": "rivers_%vv.nc", "coordinate_file": "grid.nc"},
            "Cannot use variable name templating while reading a list of files",
        ),
        (
            JulesRiversProps,
            {"read_list": True, "file": "files.txt"},
            "file to read coordinates from must be specified",
        ),
        (
            JulesRiversProps,
            {"read_list": True, "coordinate_file": "grid.nc"},
            "there has to be a file specified to read",
        ),
        (
            ImogenRunList,
            {"change_metdata_method": 2, "land_feed_co2": True},
            "land_feed_co2 is not available when change_metdata_method is"
            " prescribed_anomalies",
        ),
        (
            ImogenRunList,
            {"change_metdata_method": 3, "c_emissions": True},
            "c_emissions is not available when change_metdata_method is"
            " global_temperature_patterns",
        ),
    ],
)
def test_block_level_fail_if(model_cls, kwargs, message):
    with pytest.raises(ValidationError, match=message):
        model_cls(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"npft": 5, "nnvg": 4, "brd_leaf": 6}, "less than or equal to npft"),
        ({"npft": 5, "nnvg": 4, "soil": 10}, "less than or equal to npft\\+nnvg"),
        ({"npft": 5, "nnvg": 4, "soil": 3}, "grouped together first"),
        (
            {"npft": 5, "nnvg": 4, "urban": 6, "urban_canyon": 7, "urban_roof": 8},
            "urban cannot be combined",
        ),
        ({"npft": 5, "nnvg": 4, "urban_canyon": 7}, "canyon and roof"),
        (
            {"npft": 5, "nnvg": 4, "usr_type": [3, 10]},
            r"usr_type\[1\]: Pseudo level must be less than or equal to npft\+nnvg",
        ),
        (
            {"npft": 5, "nnvg": 4, "usr_type": [0]},
            r"usr_type\[0\]: Pseudo level must be greater than or equal to 1",
        ),
    ],
)
def test_surface_type_pseudo_levels(kwargs, message):
    with pytest.raises(ValidationError, match=message):
        JulesSurfaceTypes(**kwargs)


def test_valid_surface_type_layout_is_accepted():
    """The Loobos layout: PFTs 1-5, then urban, lake, soil, ice."""
    JulesSurfaceTypes(
        npft=5, nnvg=4, brd_leaf=1, shrub=5, urban=6, lake=7, soil=8, ice=9
    )


def test_elevated_types_accept_the_minus_one_sentinel():
    JulesSurfaceTypes(npft=5, nnvg=4, elev_ice=-1, elev_rock=-1)


def test_usr_type_may_be_numbered_among_the_pfts():
    """The user guide permits `usr_type` the whole of `1:ntype`."""
    JulesSurfaceTypes(npft=5, nnvg=4, usr_type=[3])


def test_usr_type_is_an_array_of_positions():
    """`usr_type` is `integer, length=:`, unlike every other identifier."""
    config = JulesSurfaceTypes(npft=5, nnvg=4, usr_type=[3, 6, 9])
    assert config.usr_type == [3, 6, 9]


def test_a_scalar_usr_type_is_coerced_to_a_one_element_array():
    """Fortran writes a one-element array indistinguishably from a scalar."""
    assert JulesSurfaceTypes.model_validate(
        {"npft": 5, "nnvg": 4, "usr_type": 3}
    ).usr_type == [3]


# --------------------------------------------------------------------------
# fail-if, across namelists
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "jules_soil_biogeochem": {
                    "jules_soil_biogeochem": {"soil_bgc_model": 1}
                },
                "jules_vegetation": {"jules_vegetation": {"l_triffid": True}},
            },
            "1-pool with TRIFFID",
        ),
        (
            {
                "jules_soil_biogeochem": {
                    "jules_soil_biogeochem": {"soil_bgc_model": 2}
                },
            },
            "4-pool soil C without TRIFFID",
        ),
        (
            {
                "jules_soil_biogeochem": {
                    "jules_soil_biogeochem": {"soil_bgc_model": 3}
                },
            },
            "ECOSSE without TRIFFID",
        ),
        (
            {
                "jules_irrig": {"jules_irrig": {"l_irrig_dmd": True}},
                "jules_soil": {"jules_soil": {"l_holdwater": True}},
            },
            "l_holdwater",
        ),
        (
            {
                "jules_irrig": {
                    "jules_irrig": {"l_irrig_dmd": True, "l_irrig_limit": True}
                },
            },
            "l_rivers must TRUE",
        ),
        (
            {
                "jules_soil": {"jules_soil": {"l_tile_soil": True}},
                "model_environment": {"jules_model_environment": {"l_jules_parent": 1}},
            },
            "Not available in the UM",
        ),
        (
            {
                "jules_vegetation": {"jules_vegetation": {"l_sugar": True}},
                "model_environment": {"jules_model_environment": {"l_jules_parent": 1}},
            },
            "SUGAR is not available",
        ),
        (
            {"jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 1}}},
            "UM_TRIP is not compatible with standalone",
        ),
        (
            {"jules_surface": {"jules_surface": {"iscrntdiag": 2}}},
            "preferred option in standalone",
        ),
        (
            {
                "jules_vegetation": {
                    "jules_vegetation": {"l_triffid": True, "l_red": True}
                },
                "jules_soil_biogeochem": {
                    "jules_soil_biogeochem": {"soil_bgc_model": 2}
                },
                "jules_surface_types": {
                    "jules_surface_types": {"npft": 5, "nnvg": 4, "ncpft": 2}
                },
            },
            "RED cannot be used with crop PFTs",
        ),
        (
            {"jules_vegetation": {"jules_vegetation": {"fsmc_shape": 1}}},
            "const_z = T and l_use_pft_psi = T",
        ),
        (
            {
                "urban": {"jules_urban": {"l_moruses_albedo": True}},
                "jules_radiation": {"jules_radiation": {"l_cosz": False}},
            },
            "Requires l_cosz = TRUE",
        ),
        (
            {"jules_surface": {"jules_surface": {"l_urban2t": True}}},
            "canyon and a roof surface type",
        ),
        (
            {
                "jules_deposition": {"jules_deposition": {"l_deposition": True}},
                "jules_surface": {"jules_surface": {"l_aggregate": True}},
            },
            "aggregated tile",
        ),
        (
            {"imogen": {"imogen_onoff_switch": {"l_imogen": True}}},
            "should be .true. in IMOGEN",
        ),
    ],
)
def test_cross_namelist_fail_if(overrides, message):
    with pytest.raises(ValidationError, match=message):
        build(**overrides)


UM = {"model_environment": {"jules_model_environment": {"l_jules_parent": 1}}}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"jules_vegetation": {"jules_vegetation": {"l_red": True}}}, "RED is not"),
        (
            {"jules_vegetation": {"jules_vegetation": {"fsmc_shape": 1}}},
            "not currently available to the UM",
        ),
        (
            {"jules_vegetation": {"jules_vegetation": {"stomata_model": 3}}},
            "sox is not available to the UM",
        ),
        (
            {
                "jules_water_resources": {
                    "jules_water_resources": {"l_water_resources": True}
                }
            },
            "Must be false in the UM",
        ),
        (
            {
                "jules_surface_types": {
                    "jules_surface_types": {"npft": 5, "nnvg": 4, "ncpft": 2}
                }
            },
            "not available to the UM",
        ),
        (
            {
                "jules_irrig": {
                    "jules_irrig": {"l_irrig_dmd": True, "l_irrig_limit": True}
                },
                "jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 3}},
                "jules_hydrology": {
                    "jules_hydrology": {
                        "l_hydrology": True,
                        "l_top": True,
                        "zw_max": 6.0,
                        "ti_max": 10.0,
                        "ti_wetl": 1.5,
                        "nfita": 20,
                    }
                },
            },
            "not tested in the UM",
        ),
        (
            {"jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 3}}},
            "only options compatible with the UM",
        ),
    ],
)
def test_um_only_fail_if(overrides, message):
    """Options JULES refuses when it is driven by the UM."""
    with pytest.raises(ValidationError, match=message):
        build(**UM, **overrides)


def test_overbank_inundation_is_standalone_only():
    with pytest.raises(ValidationError, match="Overbank inundation"):
        build(
            **UM,
            jules_rivers={
                "jules_rivers": {"l_rivers": True, "i_river_vn": 2},
                "jules_overbank": {"l_riv_overbank": True},
            },
        )


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (
            {"jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 2}}},
            "i_river_vn must be 3",
        ),
        (
            {
                "jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 3}},
                "jules_hydrology": {"jules_hydrology": {"l_top": False}},
            },
            "l_top must TRUE",
        ),
        (
            {
                "jules_rivers": {"jules_rivers": {"l_rivers": True, "i_river_vn": 3}},
                "jules_hydrology": {
                    "jules_hydrology": {
                        "l_hydrology": True,
                        "l_top": True,
                        "zw_max": 6.0,
                        "ti_max": 10.0,
                        "ti_wetl": 1.5,
                        "nfita": 20,
                    }
                },
                "jules_water_resources": {
                    "jules_water_resources": {
                        "l_water_resources": True,
                        "l_water_irrigation": True,
                    }
                },
            },
            "l_irrig_limit must be F",
        ),
    ],
)
def test_irrigation_limit_prerequisites(extra, message):
    with pytest.raises(ValidationError, match=message):
        build(
            jules_irrig={"jules_irrig": {"l_irrig_dmd": True, "l_irrig_limit": True}},
            **extra,
        )


def test_imogen_start_date_must_be_new_year():
    with pytest.raises(ValidationError, match="00:00:00 on 1st Jan"):
        build(
            imogen={"imogen_onoff_switch": {"l_imogen": True}},
            timesteps={
                "jules_time": {
                    "l_360": True,
                    "main_run_start": "1997-03-01 00:00:00",
                }
            },
        )


def test_two_tile_urban_needs_urban_properties():
    with pytest.raises(ValidationError, match="Urban properties need to be supplied"):
        build(
            jules_surface_types={
                "jules_surface_types": {
                    "npft": 5,
                    "nnvg": 4,
                    "urban_canyon": 6,
                    "urban_roof": 7,
                }
            },
        )


def test_minimal_config_still_validates():
    """The new rules must not reject a config built entirely from defaults."""
    build()


# --------------------------------------------------------------------------
# trigger
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_cls", "kwargs", "member"),
    [
        (JulesSoilBiogeochem, {"soil_bgc_model": 2, "kaps": 1.0}, "kaps"),
        (JulesSoilBiogeochem, {"soil_bgc_model": 1, "sorp": 1.0}, "sorp"),
        (JulesSoilBiogeochem, {"k2_ch4": 1.0}, "k2_ch4"),
        (JulesSoilBiogeochem, {"tau_ch4": 1.0}, "tau_ch4"),
        (JulesHydrology, {"l_hydrology": True, "b_pdm": 1.0}, "b_pdm"),
        (JulesHydrology, {"l_hydrology": True, "zw_max": 1.0}, "zw_max"),
        (JulesRadiation, {"l_niso_direct": True}, "l_niso_direct"),
        (JulesSoil, {"dzdeep": 1.0}, "dzdeep"),
        (JulesIrrig, {"irr_crop": 2}, "irr_crop"),
        (JulesIrrig, {"l_irrig_dmd": True, "nirrtile": 2}, "nirrtile"),
        (JulesSnow, {"snowliqcap": 0.9}, "snowliqcap"),
        (JulesSurface, {"i_aggregate_opt": 1}, "i_aggregate_opt"),
        (JulesWaterResources, {"l_water_domestic": True}, "l_water_domestic"),
        (JulesVegetation, {"triffid_period": 10}, "triffid_period"),
        (JulesVegetation, {"phenol_period": 10}, "phenol_period"),
        (JulesRivers, {"cland": 0.4}, "cland"),
        (
            JulesRivers,
            {"l_rivers": True, "i_river_vn": 2, "rivers_speed": 0.4},
            "rivers_speed",
        ),
    ],
)
def test_trigger_warns_about_an_inactive_member(model_cls, kwargs, member):
    messages = inactive(model_cls, **kwargs)
    assert any(f"'{member}'" in message for message in messages), messages


@pytest.mark.parametrize(
    ("model_cls", "kwargs"),
    [
        (JulesSoilBiogeochem, {"soil_bgc_model": 1, "kaps": 1.0}),
        (JulesSoilBiogeochem, {"soil_bgc_model": 2, "sorp": 1.0}),
        (JulesHydrology, {"l_hydrology": True, "l_pdm": True, "b_pdm": 1.0}),
        (JulesSoil, {"l_bedrock": True, "dzdeep": 1.0}),
        (JulesIrrig, {"l_irrig_dmd": True, "irr_crop": 2}),
        (JulesSnow, {"nsmax": 3, "dzsnow": [0.1, 0.2, 0.2], "snowliqcap": 0.9}),
        (JulesRivers, {"l_rivers": True, "i_river_vn": 2, "cland": 0.4}),
    ],
)
def test_no_warning_when_the_member_is_active(model_cls, kwargs):
    assert inactive(model_cls, **kwargs) == []


def test_default_values_never_warn():
    """Every block built from its defaults alone must be silent."""
    for model_cls in (
        JulesSoilBiogeochem,
        JulesHydrology,
        JulesRadiation,
        JulesSoil,
        JulesIrrig,
        JulesSnow,
        JulesSurface,
        JulesWaterResources,
        JulesVegetation,
        JulesRivers,
    ):
        assert inactive(model_cls) == [], model_cls.__name__


def test_inactive_warning_is_escalatable():
    with warnings.catch_warnings():
        warnings.simplefilter("error", InactiveNamelistKeyWarning)
        with pytest.raises(InactiveNamelistKeyWarning, match="ignore it because"):
            JulesSoilBiogeochem(soil_bgc_model=SoilBgcModel.four_pool, kaps=1.0)


def test_cross_namelist_trigger_warns():
    """`l_top` gates the methane members that live in another namelist."""
    data = minimal_valid()
    data["jules_soil_biogeochem"] = {
        "jules_soil_biogeochem": {"ch4_substrate": 2, "soil_bgc_model": 1}
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        JulesNamelists.model_validate(data)
    messages = [
        str(record.message)
        for record in caught
        if issubclass(record.category, InactiveNamelistKeyWarning)
    ]
    assert any("'ch4_substrate'" in message for message in messages), messages


# --------------------------------------------------------------------------
# the shapes the new river-routing and IMOGEN rules must *not* reject
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        # the shape every real routing app uses: one file, no templating
        {"file": "rivers.nc", "coordinate_file": "rivers.nc", "nvars": 0},
        # a list of files, with the coordinates named separately
        {"read_list": True, "file": "file_list.txt", "coordinate_file": "grid.nc"},
        # templating, with the coordinates named separately
        {"file": "rivers_%vv.nc", "coordinate_file": "grid.nc"},
    ],
)
def test_river_props_file_sources_that_are_legal(kwargs):
    JulesRiversProps(**kwargs)


def test_imogen_feedbacks_are_legal_with_the_analogue_model():
    """Method 1 is the one that supports every feedback."""
    ImogenRunList(
        change_metdata_method=ChangeMetdataMethod.analogue_patterns,
        land_feed_co2=True,
        land_feed_ch4=True,
        ocean_feed=True,
        c_emissions=True,
        include_non_co2_radf=True,
    )


def test_imogen_prescribed_anomalies_accept_the_switches_turned_off():
    ImogenRunList(
        change_metdata_method=ChangeMetdataMethod.prescribed_anomalies,
        c_emissions=False,
        include_non_co2_radf=False,
    )
