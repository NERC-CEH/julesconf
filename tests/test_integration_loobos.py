"""Integration tests against the real Loobos configuration.

This is the **only** module that reads `examples/`. Commit `4e0678d`
deliberately decoupled the test suite from the example data, and unit tests
should stay self-contained; but the round-trip gates are close to meaningless
against a synthetic minimal config, which has no `nvars` blocks, no populated
lists and no enum values. Loobos exercises 6 `nvars` blocks, all 29 files and
`npft=5` / `nnvg=4`.

Loobos does **not** exercise crops or TRIFFID: `crop_params.nml` and
`triffid_params.nml` are both empty and `ncpft` is unset, so `nnpft == npft`
and the `[[crop_pft]]` half of the grouped form never runs here. That cover
lives in `test_toml_grouped.py`, and the two must be read together.

See the "Test suite" section of `notes/toml_config.md`.
"""

import warnings
from pathlib import Path

import pytest
from conftest import assert_superset, flatten

from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists, UnknownNamelistKeyWarning

LOOBOS = Path(__file__).resolve().parent.parent / "examples" / "loobos" / "namelists"

pytestmark = pytest.mark.skipif(
    not LOOBOS.is_dir(), reason="Loobos example data not present"
)


@pytest.fixture(scope="module")
def loobos_raw() -> dict:
    """The Loobos namelists as read from disk."""
    return NamelistConfig().read(LOOBOS)


@pytest.fixture(scope="module")
def loobos() -> JulesNamelists:
    """The validated Loobos configuration."""
    return JulesNamelists.from_namelists(LOOBOS)


def test_loobos_validates(loobos):
    """A real JULES configuration passes validation."""
    assert loobos.jules_surface_types.jules_surface_types.npft == 5
    assert loobos.jules_surface_types.jules_surface_types.nnvg == 4


def test_loobos_has_no_unknown_members():
    """Schema coverage is complete for a real config.

    If this starts failing, julesconf gained a coverage gap against real-world
    usage -- and those members would be silently dropped on write.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        JulesNamelists.from_namelists(LOOBOS)
    unknown = [w for w in caught if issubclass(w.category, UnknownNamelistKeyWarning)]
    assert not unknown, [str(w.message) for w in unknown]


def test_loobos_strict_read_succeeds():
    """The strict read path accepts a real configuration."""
    JulesNamelists.from_namelists(LOOBOS, strict=True)


# ---------------------------------------------------------------------------
# G1 -- namelists round-trip
# ---------------------------------------------------------------------------


def test_round_trip_preserves_every_member(tmp_path, loobos, loobos_raw):
    """Nothing in the real config is lost or altered by a write."""
    loobos.to_namelists(tmp_path, overwrite_ok=True)
    assert_superset(loobos_raw, NamelistConfig().read(tmp_path))


def test_round_trip_adds_defaults(tmp_path, loobos, loobos_raw):
    """The written config states substantially more than the input did."""
    loobos.to_namelists(tmp_path, overwrite_ok=True)
    written = flatten(NamelistConfig().read(tmp_path))
    assert len(written) > len(flatten(loobos_raw))


def test_written_config_revalidates(tmp_path, loobos):
    """The output is itself a valid JULES config -- the write path is closed."""
    loobos.to_namelists(tmp_path, overwrite_ok=True)
    JulesNamelists.from_namelists(tmp_path, strict=True)


def test_round_trip_is_idempotent(tmp_path, loobos):
    """Writing twice changes nothing the second time."""
    first, second = tmp_path / "first", tmp_path / "second"
    loobos.to_namelists(first, overwrite_ok=True)
    JulesNamelists.from_namelists(first).to_namelists(second, overwrite_ok=True)

    assert NamelistConfig().read(first) == NamelistConfig().read(second)


# ---------------------------------------------------------------------------
# G2 -- TOML is a lossless intermediate
# ---------------------------------------------------------------------------


def test_toml_round_trip_matches_direct_write(tmp_path, loobos):
    """namelists -> flat TOML -> namelists equals namelists -> namelists."""
    direct, via_toml = tmp_path / "direct", tmp_path / "via_toml"
    loobos.to_namelists(direct, overwrite_ok=True)

    toml_path = tmp_path / "loobos.toml"
    loobos.to_toml(toml_path, grouped=False)
    JulesNamelists.from_toml(toml_path).to_namelists(via_toml, overwrite_ok=True)

    assert NamelistConfig().read(direct) == NamelistConfig().read(via_toml)


def test_toml_preserves_every_member(tmp_path, loobos, loobos_raw):
    """The flat TOML form loses nothing from the original namelists."""
    toml_path = tmp_path / "loobos.toml"
    loobos.to_toml(toml_path, grouped=False)

    out = tmp_path / "out"
    JulesNamelists.from_toml(toml_path).to_namelists(out, overwrite_ok=True)
    assert_superset(loobos_raw, NamelistConfig().read(out))


# ---------------------------------------------------------------------------
# Q1 -- the grouped form round-trips real data
# ---------------------------------------------------------------------------


def test_grouped_toml_round_trip_matches_direct_write(tmp_path, loobos):
    """namelists -> grouped TOML -> namelists equals namelists -> namelists."""
    direct, via_toml = tmp_path / "direct", tmp_path / "via_toml"
    loobos.to_namelists(direct, overwrite_ok=True)

    toml_path = tmp_path / "loobos.toml"
    loobos.to_toml(toml_path, grouped=True)
    JulesNamelists.from_toml(toml_path).to_namelists(via_toml, overwrite_ok=True)

    assert NamelistConfig().read(direct) == NamelistConfig().read(via_toml)


def test_grouped_toml_preserves_every_member(tmp_path, loobos, loobos_raw):
    """Nothing in the real config is lost by the pivot."""
    toml_path = tmp_path / "loobos.toml"
    loobos.to_toml(toml_path, grouped=True)

    out = tmp_path / "out"
    JulesNamelists.from_toml(toml_path).to_namelists(out, overwrite_ok=True)
    assert_superset(loobos_raw, NamelistConfig().read(out))


def test_grouped_toml_replaces_the_pivoted_tables(loobos):
    """The five tables the pivot subsumes are gone, replaced by the arrays."""
    grouped = loobos.to_toml_dict(grouped=True)

    for table in ("pft_params", "nveg_params", "jules_surface_types"):
        assert table not in grouped
    assert [e["type"] for e in grouped["pft"]] == [
        "brd_leaf",
        "ndl_leaf",
        "c3_grass",
        "c4_grass",
        "shrub",
    ]
    assert [e["type"] for e in grouped["nvg"]] == ["urban", "lake", "soil", "ice"]
    assert "crop_pft" not in grouped  # ncpft = 0


def test_grouped_toml_is_smaller_than_the_flat_form(tmp_path, loobos):
    """The pivot exists to reduce what a user has to read."""
    flat, grouped = tmp_path / "flat.toml", tmp_path / "grouped.toml"
    loobos.to_toml(flat, grouped=False)
    loobos.to_toml(grouped, grouped=True)

    assert len(grouped.read_text().splitlines()) < len(flat.read_text().splitlines())


# ---------------------------------------------------------------------------
# PerElementDefault against real data
# ---------------------------------------------------------------------------


def test_per_element_defaults_fill_real_nvars_blocks(loobos):
    """Loobos omits several per-element fields; all are expanded on write."""
    written = flatten(loobos.to_namelist_dict())

    # nvars = 9, and loobos does not set var_name for this block.
    assert written["ancillaries.jules_soil_props.var_name"] == [""] * 9
    # npft = 5, and loobos does not set cansnowpft at all.
    assert written["jules_snow.jules_snow.cansnowpft"] == [False] * 5


def test_explicit_values_in_real_config_are_preserved(loobos):
    """Loobos sets output_type via Fortran repeat syntax; it must not be replaced."""
    written = flatten(loobos.to_namelist_dict())
    assert written["output.jules_output_profile.output_type"] == ["M"] * 22
