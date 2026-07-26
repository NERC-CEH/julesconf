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
from julesconf.schemas._grouped import CropPft, Nvg, Pft
from julesconf.schemas._namelists import find_list_len, find_per_element_default
from julesconf.schemas.constraints import (
    LIST_LEN_DIMS,
    SIBLING_DIMS,
    ListLen,
    PerElementDefault,
)


def _with_profile(**profile) -> dict:
    """A minimal config carrying one `jules_output_profile` block."""
    data = minimal_valid()
    data["output"] = {"jules_output_profile": profile}
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
        match=r"output\.jules_output_profile\.var has 3 element\(s\),"
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
    data["jules_irrig"] = {"jules_irrig": {"irrigtiles": [1, 2, 3]}}
    JulesNamelists.model_validate(data)


def test_unset_list_skips_the_check():
    """A member the user left unset is not a zero-length list."""
    JulesNamelists.model_validate(_with_profile(nvars=2, var=["smcl", "t_soil"]))


# ---------------------------------------------------------------------------
# Coexistence with PerElementDefault
# ---------------------------------------------------------------------------


def test_both_markers_are_found_on_one_field():
    info = type(
        JulesNamelists.model_validate(minimal_valid()).output.jules_output_profile
    ).model_fields["output_type"]
    assert find_list_len(info) == ListLen("nvars")
    assert find_per_element_default(info) == PerElementDefault("S", "nvars")


def test_marked_field_still_expands_on_write():
    config = JulesNamelists.model_validate(
        _with_profile(nvars=3, var=["smcl", "t_soil", "gpp"])
    )
    written = config.to_namelist_dict()["output"]["jules_output_profile"]
    assert written["output_type"] == ["S", "S", "S"]


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
            block = block.model_fields[part].annotation
        assert meta.dim in block.model_fields, path


def test_list_len_accepts_sibling_dims():
    assert ListLen("nvars").dim == "nvars"
    assert set(LIST_LEN_DIMS).isdisjoint(SIBLING_DIMS)


def test_list_len_still_rejects_an_unknown_dim():
    with pytest.raises(ValueError, match="Unknown ListLen dim 'nvar'"):
        ListLen("nvar")
