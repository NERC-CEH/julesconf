"""Behavioural tests for the grouped TOML form (Phase 2 gates Q1-Q8).

Loobos has `ncpft = 0` and empty `crop_params.nml` / `triffid_params.nml`, so
the integration round-trip exercises none of the `[[crop_pft]]` or `nnpft`
machinery. The synthetic crop fixtures here are the only cover for it.
"""

import copy
import warnings

import pytest
from conftest import flatten, minimal_grouped, minimal_valid
from hypothesis import given
from hypothesis import strategies as st

from julesconf.schemas import JulesNamelists, UnknownNamelistKeyWarning
from julesconf.schemas._grouped import (
    SPECS_BY_DIM,
    CropPft,
    GroupedConfigError,
    Nvg,
    Pft,
    ToleratedLengthWarning,
    assemble,
    disassemble,
    is_grouped,
)


def build(**kwargs) -> JulesNamelists:
    """Validate a grouped config dict."""
    return JulesNamelists.model_validate(assemble(minimal_grouped(**kwargs)))


# ---------------------------------------------------------------------------
# Q3 -- dimensions derived from array lengths, crop PFTs ordered last
# ---------------------------------------------------------------------------


def test_dimensions_are_derived_from_array_lengths():
    config = build(n_pft=3, n_crop=2, n_nvg=4)
    surface = config.jules_surface_types.jules_surface_types

    assert (surface.npft, surface.ncpft, surface.nnvg) == (5, 2, 4)


def test_npft_arrays_are_ordered_natural_then_crop():
    """`[[pft]]` entries occupy the leading positions, crops the trailing ones."""
    data = minimal_grouped(n_pft=2, n_crop=2)
    for i, entry in enumerate(data["pft"] + data["crop_pft"]):
        entry["canht_ft"] = float(i)

    config = JulesNamelists.model_validate(assemble(data))
    assert config.pft_params.jules_pftparm.canht_ft_io == [0.0, 1.0, 2.0, 3.0]


def test_nnpft_arrays_cover_natural_pfts_only():
    """TRIFFID parameters come from `[[pft]]` and are `nnpft` long."""
    data = minimal_grouped(n_pft=2, n_crop=2)
    for i, entry in enumerate(data["pft"]):
        entry["g_area"] = float(i)

    config = JulesNamelists.model_validate(assemble(data))
    assert config.triffid_params.jules_triffid.g_area_io == [0.0, 1.0]


def test_ncpft_arrays_cover_crop_pfts_only():
    data = minimal_grouped(n_pft=2, n_crop=2)
    for i, entry in enumerate(data["crop_pft"]):
        entry["t_bse"] = float(i)

    config = JulesNamelists.model_validate(assemble(data))
    assert config.crop_params.jules_cropparm.t_bse_io == [0.0, 1.0]


def test_grouped_form_needs_at_least_one_natural_pft():
    """JULES requires `ncpft < npft`, so a crop-only config is invalid."""
    with pytest.raises(GroupedConfigError, match="at least one \\[\\[pft\\]\\]"):
        build(n_pft=0, n_crop=2)


# ---------------------------------------------------------------------------
# Q4 -- all-or-none specification
# ---------------------------------------------------------------------------


def test_partial_specification_within_a_group_is_rejected():
    data = minimal_grouped(n_pft=3)
    data["pft"][0]["neff"] = 0.8e-3
    data["pft"][2]["neff"] = 0.8e-3

    with pytest.raises(GroupedConfigError) as exc:
        assemble(data)

    message = str(exc.value)
    assert "cannot be partially specified" in message
    assert "pft[1]" in message
    assert "omits 'neff'" in message
    assert "pft[0]" in message


def test_partial_specification_across_pft_and_crop_is_rejected():
    """An `npft` parameter spans both tables, so both must set it."""
    data = minimal_grouped(n_pft=2, n_crop=1)
    for entry in data["pft"]:
        entry["canht_ft"] = 1.0

    with pytest.raises(GroupedConfigError, match=r"crop_pft\[0\].*omits 'canht_ft'"):
        assemble(data)


def test_error_names_the_entry_by_label():
    data = minimal_grouped(n_pft=2)
    data["pft"][0]["name"] = "broadleaf"
    data["pft"][0]["neff"] = 0.8e-3

    with pytest.raises(GroupedConfigError, match="'broadleaf'"):
        assemble(data)


def test_multiple_violations_are_reported_together():
    data = minimal_grouped(n_pft=2)
    data["pft"][0].update({"neff": 0.8e-3, "lai": 5.0, "kext": 0.5})

    with pytest.raises(GroupedConfigError) as exc:
        assemble(data)

    for field in ("neff", "lai", "kext"):
        assert field in str(exc.value)


# ---------------------------------------------------------------------------
# Q5 -- ntype assembly spans both groups, PFTs first
# ---------------------------------------------------------------------------


def test_ntype_pivots_tile_map_ids_but_not_the_repeated_rsurf_std():
    """Every pivotable `ntype` member pivots, and `rsurf_std_io` is not one.

    `JULES_DEPOSITION_SPECIES` is a repeated group, so each species carries its
    own `ntype`-long surface-resistance array and there is no single value a
    `[[pft]]` entry could hold; it stays in the flat form.
    `JULES_DEPOSITION_SPECIES_SPECIFIC` is read once, so its four `ntype`
    arrays pivot like `tile_map_ids` does, onto every group in turn.
    """
    assert {spec.member for spec in SPECS_BY_DIM["ntype"]} == {
        "tile_map_ids",
        "ch4_up_flux_io",
        "h2dd_c_io",
        "h2dd_m_io",
        "h2dd_q_io",
    }
    assert "rsurf_std" not in set(Pft.model_fields) | set(Nvg.model_fields)
    for model in (Pft, CropPft, Nvg):
        assert "tile_map_ids" in model.model_fields


def test_ntype_member_concatenates_across_all_three_groups():
    """An `ntype` field spans natural PFTs, then crops, then non-vegetated."""
    data = minimal_grouped(n_pft=2, n_crop=1, n_nvg=2)
    for i, entry in enumerate(data["pft"] + data["crop_pft"] + data["nvg"]):
        entry["tile_map_ids"] = i + 1

    config = JulesNamelists.model_validate(assemble(data))
    assert config.jules_surface_types.jules_surface_types.tile_map_ids == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_dimension_fields_concatenate_pfts_then_non_veg():
    """Order across groups: natural PFTs, then crops, then non-vegetated."""
    data = minimal_grouped(n_pft=2, n_crop=1, n_nvg=2)
    for i, entry in enumerate(data["pft"] + data["crop_pft"]):
        entry["canht_ft"] = float(i)
    for i, entry in enumerate(data["nvg"]):
        entry["albsnc_nvg"] = float(i)

    config = JulesNamelists.model_validate(assemble(data))
    assert config.pft_params.jules_pftparm.canht_ft_io == [0.0, 1.0, 2.0]
    assert config.nveg_params.jules_nvegparm.albsnc_nvg_io == [0.0, 1.0]


# ---------------------------------------------------------------------------
# Q6 -- the two forms are mutually exclusive
# ---------------------------------------------------------------------------


def test_grouped_and_flat_parameter_together_is_rejected():
    data = minimal_grouped()
    data["pft_params"] = {"jules_pftparm": {"canht_ft_io": [1.0, 2.0]}}

    with pytest.raises(GroupedConfigError, match="canht_ft_io"):
        assemble(data)


def test_grouped_and_flat_dimension_together_is_rejected():
    data = minimal_grouped()
    data["jules_surface_types"] = {"jules_surface_types": {"npft": 2}}

    with pytest.raises(GroupedConfigError, match="npft"):
        assemble(data)


def test_sentinel_index_members_survive_alongside_the_grouped_form():
    """A "not in use" sentinel is not a position, so it is not a conflict."""
    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["jules_surface_types"] = {"jules_surface_types": {"elev_ice": -1}}

    flat = assemble(data)
    assert flat["jules_surface_types"]["jules_surface_types"]["elev_ice"] == -1


# ---------------------------------------------------------------------------
# Q8 -- surface type index members
# ---------------------------------------------------------------------------


def test_index_members_are_reconstructed_from_type_and_position():
    config = build(n_pft=2, n_nvg=2)
    surface = config.jules_surface_types.jules_surface_types

    assert (surface.brd_leaf, surface.ndl_leaf) == (1, 2)
    assert (surface.urban, surface.lake) == (3, 4)


def test_crop_pfts_are_indexed_after_natural_pfts():
    data = minimal_grouped(n_pft=2, n_crop=1, n_nvg=1)
    data["crop_pft"][0]["type"] = "c3_crop"

    config = JulesNamelists.model_validate(assemble(data))
    surface = config.jules_surface_types.jules_surface_types
    assert surface.c3_crop == 3
    assert surface.urban == 4


def test_entry_without_a_type_contributes_no_index_member():
    data = minimal_grouped(n_pft=2, n_nvg=2)
    del data["pft"][1]["type"]

    config = JulesNamelists.model_validate(assemble(data))
    surface = config.jules_surface_types.jules_surface_types
    assert surface.brd_leaf == 1
    assert surface.ndl_leaf is None
    assert surface.urban == 3


def test_duplicate_surface_type_is_rejected():
    """Each index member holds one integer, so a type cannot be reused."""
    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["nvg"][1]["type"] = "urban"

    with pytest.raises(GroupedConfigError, match="'urban' is already used"):
        assemble(data)


def test_non_vegetated_type_on_a_pft_entry_is_rejected():
    data = minimal_grouped(n_pft=2)
    data["pft"][0]["type"] = "urban"

    with pytest.raises(GroupedConfigError, match="not a vegetated surface type"):
        assemble(data)


def test_vegetated_type_on_an_nvg_entry_is_rejected():
    data = minimal_grouped(n_pft=2)
    data["nvg"][0]["type"] = "brd_leaf"

    with pytest.raises(GroupedConfigError, match="not a non-vegetated surface"):
        assemble(data)


def test_usr_type_is_accepted_in_either_group():
    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["pft"][1]["type"] = "usr_type"
    assert assemble(data)

    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["nvg"][1]["type"] = "usr_type"
    assert assemble(data)


def test_elevated_ice_may_claim_several_positions():
    """`elev_ice` is an array too: one entry per elevation band."""
    data = minimal_grouped(n_pft=2, n_nvg=3)
    data["nvg"][1]["type"] = "elev_ice"
    data["nvg"][2]["type"] = "elev_ice"

    flat = assemble(data)
    assert flat["jules_surface_types"]["jules_surface_types"]["elev_ice"] == [4, 5]


def test_a_multi_band_elev_ice_round_trips_through_the_grouped_form():
    data = minimal_grouped(n_pft=2, n_nvg=3)
    data["nvg"][1]["type"] = "elev_ice"
    data["nvg"][2]["type"] = "elev_ice"
    expected = copy.deepcopy(data["nvg"])

    assert disassemble(assemble(data))["nvg"] == expected


def test_usr_type_may_claim_several_positions():
    """It is the one identifier JULES holds as an array, not a scalar."""
    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["pft"][1]["type"] = "usr_type"
    data["nvg"][1]["type"] = "usr_type"

    flat = assemble(data)
    assert flat["jules_surface_types"]["jules_surface_types"]["usr_type"] == [2, 4]


def test_a_multi_position_usr_type_round_trips_through_the_grouped_form():
    data = minimal_grouped(n_pft=2, n_nvg=2)
    data["pft"][1]["type"] = "usr_type"
    data["nvg"][1]["type"] = "usr_type"
    expected = {group: copy.deepcopy(data[group]) for group in ("pft", "nvg")}
    regrouped = disassemble(assemble(data))

    assert regrouped["pft"] == expected["pft"]
    assert regrouped["nvg"] == expected["nvg"]


def test_crop_identifier_is_allowed_on_a_natural_pft():
    """Surface type identity and the crop model are independent in JULES."""
    data = minimal_grouped(n_pft=2, n_nvg=1)
    data["pft"][1]["type"] = "c3_crop"

    config = JulesNamelists.model_validate(assemble(data))
    assert config.jules_surface_types.jules_surface_types.ncpft == 0


# ---------------------------------------------------------------------------
# Q1 -- round-trip through the grouped form, including crop PFTs
# ---------------------------------------------------------------------------


def test_grouped_round_trip_with_crop_pfts(tmp_path):
    """The crop half of the pivot, which Loobos cannot cover."""
    data = minimal_grouped(n_pft=2, n_crop=2, n_nvg=2)
    for i, entry in enumerate(data["pft"] + data["crop_pft"]):
        entry["canht_ft"] = float(i + 1)
    for i, entry in enumerate(data["pft"]):
        entry["g_area"] = float(i + 1)
    for i, entry in enumerate(data["crop_pft"]):
        entry["t_bse"] = float(i + 1)

    config = JulesNamelists.model_validate(assemble(data))
    path = tmp_path / "config.toml"
    config.to_toml(path)
    reread = JulesNamelists.from_toml(path)

    assert reread.to_namelist_dict() == config.to_namelist_dict()


def test_disassemble_inverts_assemble():
    """The grouped form survives a trip through the flat one."""
    data = minimal_grouped(n_pft=2, n_crop=1, n_nvg=2)
    for i, entry in enumerate(data["pft"] + data["crop_pft"]):
        entry["canht_ft"] = float(i)

    original = {group: [dict(e) for e in data[group]] for group in ("pft", "crop_pft")}
    regrouped = disassemble(assemble(data))

    assert regrouped["pft"] == original["pft"]
    assert regrouped["crop_pft"] == original["crop_pft"]


@given(
    n_pft=st.integers(min_value=1, max_value=4),
    n_crop=st.integers(min_value=0, max_value=2),
    n_nvg=st.integers(min_value=1, max_value=3),
    values=st.lists(
        st.floats(min_value=0.0, max_value=50.0, allow_nan=False),
        min_size=6,
        max_size=6,
    ),
)
def test_assemble_disassemble_is_a_round_trip(n_pft, n_crop, n_nvg, values):
    """Property: the grouped form survives a trip through the flat one.

    `canht_ft` is set on every PFT contributor and `catch_nvg` on every
    non-vegetated one, so both a `npft` and an `nnvg` field are exercised at
    each shape.
    """
    data = minimal_grouped(n_pft=n_pft, n_crop=n_crop, n_nvg=n_nvg)
    pfts = data["pft"] + data.get("crop_pft", [])
    for i, entry in enumerate(pfts):
        entry["canht_ft"] = values[i % len(values)]
    for i, entry in enumerate(data["nvg"]):
        entry["catch_nvg"] = values[i % len(values)]

    original = {
        group: [dict(e) for e in data[group]]
        for group in ("pft", "crop_pft", "nvg")
        if group in data
    }
    regrouped = disassemble(assemble(data))

    for group, entries in original.items():
        assert regrouped[group] == entries


def test_pivoted_tables_disappear_from_the_grouped_form():
    """The five tables the pivot replaces must not also be emitted."""
    config = build(n_pft=2, n_nvg=2)
    grouped = config.to_toml_dict(grouped=True)

    for table in ("pft_params", "nveg_params", "triffid_params", "crop_params"):
        assert table not in grouped
    assert "jules_surface_types" not in grouped
    assert len(grouped["pft"]) == 2
    assert len(grouped["nvg"]) == 2


# ---------------------------------------------------------------------------
# Form detection and the flat escape hatch
# ---------------------------------------------------------------------------


def test_is_grouped_detects_each_key():
    assert not is_grouped(minimal_valid())
    assert is_grouped(minimal_grouped())
    assert is_grouped({"nvg": []})


def test_flat_form_still_round_trips(tmp_path):
    """`grouped=False` remains a working escape hatch."""
    config = JulesNamelists.model_validate(minimal_valid())
    path = tmp_path / "flat.toml"
    config.to_toml(path, grouped=False)

    assert JulesNamelists.from_toml(path).to_namelist_dict() == (
        config.to_namelist_dict()
    )


def test_unknown_parameter_on_an_entry_warns():
    data = minimal_grouped(n_pft=2)
    data["pft"][0]["nonsense"] = 1.0

    with pytest.warns(UnknownNamelistKeyWarning, match="nonsense"):
        assemble(data)


def test_strict_escalates_an_unknown_entry_parameter(tmp_path):
    """Assembly happens inside the strict filter, so typos are caught."""
    import tomli_w

    data = minimal_grouped(n_pft=2)
    data["pft"][0]["nonsense"] = 1.0
    path = tmp_path / "config.toml"
    with open(path, "wb") as f:
        tomli_w.dump(data, f)

    with pytest.raises(UnknownNamelistKeyWarning):
        JulesNamelists.from_toml(path, strict=True)


def test_grouped_form_needs_at_least_one_nvg():
    with pytest.raises(GroupedConfigError, match=r"at least one \[\[nvg\]\]"):
        build(n_pft=2, n_nvg=0)


def test_disassemble_needs_the_dimensions():
    """Without npft/nnvg there is no way to know how to split the arrays."""
    with pytest.raises(GroupedConfigError, match="without jules_surface_types"):
        disassemble({"jules_surface_types": {"jules_surface_types": {}}})


def test_disassemble_rejects_two_types_at_one_position():
    """A malformed flat config cannot be pivoted."""
    flat = minimal_valid(npft=2, nnvg=1)
    flat["jules_surface_types"]["jules_surface_types"].update(
        {"brd_leaf": 1, "ndl_leaf": 1}
    )

    with pytest.raises(GroupedConfigError, match="position 1 is claimed by both"):
        disassemble(flat)


def test_grouped_table_must_be_an_array_of_tables():
    data = minimal_grouped()
    data["pft"] = {"type": "brd_leaf"}

    with pytest.raises(GroupedConfigError, match="array of tables"):
        assemble(data)


# ---------------------------------------------------------------------------
# PerElementDefault interaction
# ---------------------------------------------------------------------------


def test_per_element_default_still_expands_under_the_grouped_form():
    """`cansnowpft` carries both `ListLen` and `PerElementDefault`."""
    config = build(n_pft=3, n_nvg=2)
    written = flatten(config.to_namelist_dict())

    assert written["jules_snow.jules_snow.cansnowpft"] == [False] * 3


def test_explicit_per_element_values_from_entries_are_preserved():
    data = minimal_grouped(n_pft=2, n_nvg=2)
    for entry in data["pft"]:
        entry["cansnowpft"] = True

    config = JulesNamelists.model_validate(assemble(data))
    written = flatten(config.to_namelist_dict())
    assert written["jules_snow.jules_snow.cansnowpft"] == [True, True]


# ---------------------------------------------------------------------------
# The tolerated-length truncation
# ---------------------------------------------------------------------------


def test_over_long_triffid_array_warns_and_truncates():
    """A legacy `npft`-length TRIFFID array loses its unread trailing values."""
    flat = minimal_valid(npft=4, nnvg=2, ncpft=2)
    flat["triffid_params"] = {"jules_triffid": {"g_area_io": [1.0, 2.0, 3.0, 4.0]}}

    with pytest.warns(ToleratedLengthWarning, match="g_area_io"):
        grouped = disassemble(flat)

    assert [e["g_area"] for e in grouped["pft"]] == [1.0, 2.0]
    assert "g_area" not in grouped["crop_pft"][0]


def test_tolerated_length_is_preserved_by_the_flat_form(tmp_path):
    """The escape hatch named in the warning actually works."""
    flat = minimal_valid(npft=4, nnvg=2, ncpft=2)
    flat["triffid_params"] = {"jules_triffid": {"g_area_io": [1.0, 2.0, 3.0, 4.0]}}
    config = JulesNamelists.model_validate(flat)

    path = tmp_path / "flat.toml"
    with warnings.catch_warnings():
        warnings.simplefilter("error", ToleratedLengthWarning)
        config.to_toml(path, grouped=False)

    reread = JulesNamelists.from_toml(path)
    assert reread.triffid_params.jules_triffid.g_area_io == [1.0, 2.0, 3.0, 4.0]
