"""Tests for namelist-local (`sibling`) `ListLen` dimensions.

`LIST_LEN_DIMS` are resolved once from `jules_surface_types`; `SIBLING_DIMS`
name a member of the *same* block, so each block is checked against its own
value. `JULES_OUTPUT_PROFILE` is the workhorse here because it carries no
hand-rolled `nvars` validator of its own, so a failure can only come from the
generic machinery under test.
"""

from typing import Any

import pytest
from conftest import minimal_valid, walk_fields
from pydantic import ValidationError

from julesconf.schemas import JulesNamelists
from julesconf.schemas._base import repeated_group_model
from julesconf.schemas._grouped import CropPft, Nvg, Pft
from julesconf.schemas._namelists import find_list_len, find_per_element_default
from julesconf.schemas.constraints import (
    LIST_LEN_DIMS,
    SIBLING_DIMS,
    ListLen,
    PerElementDefault,
)
from julesconf.schemas.jules_soil import JulesSoil


def _with_profile(*profiles, **profile) -> dict:
    """A minimal config carrying one or more `jules_output_profile` blocks.

    `jules_output_profile` is a repeated group, so it is always a list, even
    for a single profile. `nprofiles` is set to match, since the two have to
    agree.
    """
    blocks = list(profiles) or [profile]
    data = minimal_valid()
    data["output"] = {
        "jules_output": {"nprofiles": len(blocks)},
        "jules_output_profile": blocks,
    }
    return data


# ---------------------------------------------------------------------------
# Resolution against the sibling member
# ---------------------------------------------------------------------------


def test_matching_length_validates():
    JulesNamelists.model_validate(
        _with_profile(nvars=2, var=["smcl", "t_soil"], var_name=["a", "b"])
    )


def test_mismatched_length_raises_naming_the_sibling_dim():
    with pytest.raises(
        ValidationError,
        match=r"output\.jules_output_profile\(1\)\.var has 3 element\(s\),"
        r" expected nvars=2",
    ):
        JulesNamelists.model_validate(
            _with_profile(nvars=2, var=["smcl", "t_soil", "gpp"])
        )


def test_each_block_is_checked_against_its_own_nvars():
    """Two blocks naming `nvars` are unrelated; one must not fix up the other."""
    data = _with_profile(nvars=1, var=["smcl"])
    data["ancillaries"] = {
        "jules_soil_props": {"nvars": 3, "var": ["b", "sathh", "satcon"]}
    }
    JulesNamelists.model_validate(data)


def test_sibling_dim_on_another_namelist_is_not_used():
    """`nsmax` is `JULES_SNOW`'s own member, not a global dimension."""
    data = minimal_valid()
    data["jules_snow"] = {"jules_snow": {"nsmax": 3, "dzsnow": [0.1, 0.2]}}
    with pytest.raises(ValidationError, match=r"expected nsmax=3"):
        JulesNamelists.model_validate(data)


# ---------------------------------------------------------------------------
# Inactive blocks
# ---------------------------------------------------------------------------


def test_zero_sibling_skips_the_check():
    """`nvars = 0` means JULES reads nothing from the block."""
    JulesNamelists.model_validate(_with_profile(nvars=0, var=["smcl", "t_soil"]))


def test_unset_sibling_skips_the_check():
    """`nirrtile` is optional; with no value there is nothing to check against."""
    data = minimal_valid()
    data["jules_irrig"] = {
        # `irrigtiles` is only read with irrigation on and not all tiles
        # irrigated; both gates go in so the config is self-consistent.
        "jules_irrig": {
            "l_irrig_dmd": True,
            "frac_irrig_all_tiles": False,
            "irrigtiles": [1, 2, 3],
        }
    }
    JulesNamelists.model_validate(data)


def test_unset_list_skips_the_check():
    """A member the user left unset is not a zero-length list."""
    JulesNamelists.model_validate(_with_profile(nvars=2, var=["smcl", "t_soil"]))


# ---------------------------------------------------------------------------
# Coexistence with PerElementDefault
# ---------------------------------------------------------------------------


def test_both_markers_are_found_on_one_field():
    info = type(
        JulesNamelists.model_validate(_with_profile()).output.jules_output_profile[0]
    ).model_fields["output_type"]
    assert find_list_len(info) == ListLen("nvars")
    assert find_per_element_default(info) == PerElementDefault("S", "nvars")


def test_marked_field_still_expands_on_write():
    config = JulesNamelists.model_validate(
        _with_profile(nvars=3, var=["smcl", "t_soil", "gpp"])
    )
    written = config.to_namelist_dict()["output"]["jules_output_profile"]
    assert written[0]["output_type"] == ["S", "S", "S"]


def test_expanded_value_satisfies_its_own_list_len():
    """Expansion writes exactly `nvars` elements, so a re-read validates."""
    config = JulesNamelists.model_validate(
        _with_profile(nvars=3, var=["smcl", "t_soil", "gpp"])
    )
    JulesNamelists.model_validate(config.to_namelist_dict())


# ---------------------------------------------------------------------------
# Structural guards
# ---------------------------------------------------------------------------


def test_sibling_dims_stay_out_of_the_grouped_models():
    """`nvars` is not a surface-type dimension; no group may absorb its fields."""
    grouped = set(Pft.model_fields) | set(CropPft.model_fields) | set(Nvg.model_fields)
    assert not grouped & {"nvars", "var", "use_file", "const_val", "dzsnow"}


def test_sibling_dim_fields_use_the_canonical_spelling():
    """The same guard as for cross-namelist dims, restricted to the new ones."""
    non_canonical = [
        path
        for path, info in walk_fields(JulesNamelists)
        if (meta := find_list_len(info)) is not None
        and meta.dim in SIBLING_DIMS
        and not any(isinstance(m, ListLen) for m in info.metadata)
    ]
    assert non_canonical == []


def test_every_sibling_dim_names_a_real_member():
    """A sibling dim must exist as a field on every block that refers to it."""
    for path, info in walk_fields(JulesNamelists):
        meta = find_list_len(info)
        if meta is None or meta.dim not in SIBLING_DIMS:
            continue
        block: Any = JulesNamelists
        for part in path.split(".")[:-1]:
            info = block.model_fields[part.removesuffix("[]")]
            block = repeated_group_model(info.annotation) or info.annotation
        assert meta.dim in block.model_fields, path


def test_list_len_accepts_sibling_dims():
    assert ListLen("nvars").dim == "nvars"
    assert set(LIST_LEN_DIMS).isdisjoint(SIBLING_DIMS)


def test_list_len_still_rejects_an_unknown_dim():
    with pytest.raises(ValueError, match="Unknown ListLen dim 'nvar'"):
        ListLen("nvar")


# ---------------------------------------------------------------------------
# sm_levels is derived from dzsoil_io
# ---------------------------------------------------------------------------


def test_sm_levels_is_derived_from_the_layer_depths():
    """Listing the layer depths already says how many layers there are."""
    assert JulesSoil(dzsoil_io=[0.1, 0.25, 0.65, 2.0, 3.0, 4.0]).sm_levels == 6


def test_a_scalar_dzsoil_io_means_one_layer():
    """Fortran writes a one-element array indistinguishably from a scalar."""
    config = JulesSoil.model_validate({"dzsoil_io": 0.1})
    assert (config.sm_levels, config.dzsoil_io) == (1, [0.1])


def test_sm_levels_keeps_its_default_without_dzsoil_io():
    assert JulesSoil().sm_levels == 4


def test_an_explicit_sm_levels_is_never_overwritten():
    """The derivation fills a gap; it does not hide a real disagreement."""
    with pytest.raises(ValidationError, match="expected sm_levels=4"):
        JulesSoil(sm_levels=4, dzsoil_io=[0.1] * 6)


def test_a_derived_sm_levels_survives_the_namelist_round_trip():
    """`to_namelist_dict` writes `sm_levels`, so the second read agrees."""
    data = minimal_valid()
    data["jules_soil"]["jules_soil"] = {"dzsoil_io": [0.1] * 6}
    written = JulesNamelists.model_validate(data).to_namelist_dict()
    block = written["jules_soil"]["jules_soil"]
    assert block["sm_levels"] == 6
    assert JulesSoil.model_validate(block).sm_levels == 6
