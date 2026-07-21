"""Phase 1 gates: the TOML front-end and the explicit-defaults guarantee.

See the "Test suite" section of `notes/toml_config.md`.
"""

import warnings

import pytest
import tomli_w
from conftest import assert_superset, flatten, minimal_valid

from julesconf.config import NamelistConfig
from julesconf.schemas import (
    JulesNamelists,
    PostponedNamelistWarning,
    UnknownNamelistKeyWarning,
)
from julesconf.schemas.jules_soil import SoilhcMethod

# ---------------------------------------------------------------------------
# G1 / G2 -- round-trip through namelists and TOML
# ---------------------------------------------------------------------------


def test_namelist_round_trip_preserves_input(tmp_path, minimal_config):
    """Writing a config back to namelists loses nothing it was given."""
    model = JulesNamelists.model_validate(minimal_config)
    model.to_namelists(tmp_path, overwrite_ok=True)
    assert_superset(minimal_config, NamelistConfig().read(tmp_path))


def test_toml_is_a_lossless_intermediate(tmp_path, minimal_config):
    """namelists -> TOML -> namelists gives the same result as going direct."""
    model = JulesNamelists.model_validate(minimal_config)

    direct = tmp_path / "direct"
    model.to_namelists(direct, overwrite_ok=True)

    toml_path = tmp_path / "config.toml"
    model.to_toml(toml_path)
    via_toml = tmp_path / "via_toml"
    JulesNamelists.from_toml(toml_path).to_namelists(via_toml, overwrite_ok=True)

    assert NamelistConfig().read(direct) == NamelistConfig().read(via_toml)


def test_from_toml_rejects_invalid_config(tmp_path):
    """A TOML config that violates the schema fails validation."""
    data = minimal_valid()
    data["jules_surface_types"]["jules_surface_types"]["npft"] = 0  # must be >= 1
    model_path = tmp_path / "bad.toml"

    with open(model_path, "wb") as f:
        tomli_w.dump(data, f)

    with pytest.raises(ValueError, match="npft"):
        JulesNamelists.from_toml(model_path)


# ---------------------------------------------------------------------------
# G3 -- every default julesconf holds is written explicitly
# ---------------------------------------------------------------------------


def test_defaults_are_written_explicitly(tmp_path, minimal_config):
    """A field with a non-None default appears in the output even if unset."""
    JulesNamelists.model_validate(minimal_config).to_namelists(
        tmp_path, overwrite_ok=True
    )
    written = flatten(NamelistConfig().read(tmp_path))

    # None of these are in minimal_config; all have julesconf defaults.
    assert written["jules_soil.jules_soil.sm_levels"] == 4
    assert written["jules_snow.jules_snow.rho_snow_const"] is not None
    assert written["jules_soil_biogeochem.jules_soil_biogeochem.bio_hum_cn"] == 10.0
    assert written["ancillaries.jules_co2.co2_mmr"] == pytest.approx(5.241e-4)


def test_written_config_covers_all_29_namelists(tmp_path, minimal_config):
    """Every namelist file is written, including those with no set members."""
    JulesNamelists.model_validate(minimal_config).to_namelists(
        tmp_path, overwrite_ok=True
    )
    assert len(sorted(tmp_path.glob("*.nml"))) == 29


def test_no_none_values_reach_the_namelists(tmp_path, minimal_config):
    """Fields julesconf has no value for are omitted, not written as None."""
    JulesNamelists.model_validate(minimal_config).to_namelists(
        tmp_path, overwrite_ok=True
    )
    assert not [
        k for k, v in flatten(NamelistConfig().read(tmp_path)).items() if v is None
    ]


# ---------------------------------------------------------------------------
# G4 -- unschema'd members are a write-path hazard
# ---------------------------------------------------------------------------


def test_unknown_member_warns_by_default(minimal_config):
    """An unmodelled member is dropped, but not silently."""
    minimal_config["jules_soil"]["jules_soil"]["not_a_real_member"] = 1
    with pytest.warns(UnknownNamelistKeyWarning, match="not_a_real_member"):
        JulesNamelists.model_validate(minimal_config)


def test_unknown_member_is_lost_when_writing(tmp_path, minimal_config):
    """Document the hazard: a dropped member does not survive a round-trip."""
    minimal_config["jules_soil"]["jules_soil"]["not_a_real_member"] = 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnknownNamelistKeyWarning)
        model = JulesNamelists.model_validate(minimal_config)
    model.to_namelists(tmp_path, overwrite_ok=True)

    written = flatten(NamelistConfig().read(tmp_path))
    assert "jules_soil.jules_soil.not_a_real_member" not in written


def test_strict_rejects_unknown_members(tmp_path, minimal_config):
    """strict=True turns the hazard into an error before anything is written."""
    minimal_config["jules_soil"]["jules_soil"]["not_a_real_member"] = 1

    path = tmp_path / "c.toml"
    with open(path, "wb") as f:
        tomli_w.dump(minimal_config, f)

    with pytest.raises(UnknownNamelistKeyWarning, match="not_a_real_member"):
        JulesNamelists.from_toml(path, strict=True)


# ---------------------------------------------------------------------------
# G5 -- enum handling across the round-trip
# ---------------------------------------------------------------------------


def test_toml_writes_enum_names(tmp_path, minimal_config):
    """to_toml writes member names, so the config is self-documenting."""
    minimal_config["jules_soil"]["jules_soil"]["soilhc_method"] = 2
    model = JulesNamelists.model_validate(minimal_config)

    path = tmp_path / "c.toml"
    model.to_toml(path)
    assert 'soilhc_method = "peters_lidard"' in path.read_text()


def test_from_toml_accepts_enum_names_and_values(tmp_path):
    """Both spellings validate to the same enum member."""
    for spelling in ("peters_lidard", 2):
        data = minimal_valid()
        data["jules_soil"]["jules_soil"]["soilhc_method"] = spelling
        path = tmp_path / f"c_{spelling}.toml"
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
        model = JulesNamelists.from_toml(path)
        assert model.jules_soil.jules_soil.soilhc_method is SoilhcMethod.peters_lidard


def test_namelists_receive_plain_ints_for_enums(tmp_path, minimal_config):
    """f90nml must see plain ints, not enum members."""
    minimal_config["jules_soil"]["jules_soil"]["soilhc_method"] = "peters_lidard"
    JulesNamelists.model_validate(minimal_config).to_namelists(
        tmp_path, overwrite_ok=True
    )

    value = flatten(NamelistConfig().read(tmp_path))[
        "jules_soil.jules_soil.soilhc_method"
    ]
    assert value == 2
    assert type(value) is int


# ---------------------------------------------------------------------------
# G6 -- postponed namelists
# ---------------------------------------------------------------------------


def test_postponed_namelist_warns(minimal_config):
    """A postponed namelist is reported specifically, not as an unknown key."""
    minimal_config["cable_prognostics"] = {"cable_prognostics": {}}
    with pytest.warns(PostponedNamelistWarning, match="cable_prognostics"):
        JulesNamelists.model_validate(minimal_config)


def test_postponed_namelist_warning_is_independently_escalatable(minimal_config):
    """Escalating PostponedNamelistWarning does not require escalating the other."""
    minimal_config["red_params"] = {"red_params": {}}
    with warnings.catch_warnings():
        warnings.simplefilter("error", PostponedNamelistWarning)
        with pytest.raises(PostponedNamelistWarning, match="red_params"):
            JulesNamelists.model_validate(minimal_config)


def test_postponed_namelist_is_not_an_unknown_key_warning(minimal_config):
    """The two warning classes do not overlap."""
    minimal_config["oasis_rivers"] = {"oasis_rivers": {}}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        JulesNamelists.model_validate(minimal_config)
    assert not [w for w in caught if issubclass(w.category, UnknownNamelistKeyWarning)]


def test_postponed_namelist_file_is_detected_on_read(tmp_path, minimal_config):
    """A postponed .nml sitting in a namelists directory is reported."""
    JulesNamelists.model_validate(minimal_config).to_namelists(
        tmp_path, overwrite_ok=True
    )
    (tmp_path / "cable_soil.nml").write_text("&cable_soil\n/\n")

    with pytest.warns(PostponedNamelistWarning, match="cable_soil"):
        JulesNamelists.from_namelists(tmp_path)
