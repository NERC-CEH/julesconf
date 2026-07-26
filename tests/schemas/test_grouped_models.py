"""Structural tests for the generated `Pft` / `CropPft` / `Nvg` models.

These are anti-drift guards. The grouped models are generated from the
`ListLen` metadata on the flat schemas, so their failure mode is silence: a new
`ListLen` field that the generator misses simply never appears in the TOML
surface, and nothing breaks visibly. `test_generated_model_covers_exactly_its_dims`
is what makes generation safe to rely on, in the same way
`test_every_list_len_uses_canonical_spelling` guards the marker it depends on.
"""

import pytest
from conftest import walk_fields
from pydantic import ValidationError

from julesconf.schemas import JulesNamelists
from julesconf.schemas._grouped import (
    CONTRIBUTORS,
    NVG_TYPE_IDS,
    SHARED_TYPE_IDS,
    VEG_TYPE_IDS,
    CropPft,
    Nvg,
    Pft,
    _strip_io,
)
from julesconf.schemas._namelists import find_list_len
from julesconf.schemas.constraints import LIST_LEN_DIMS
from julesconf.schemas.jules_surface_types import JulesSurfaceTypes

DIMS_FOR = {
    Pft: {"npft", "nnpft", "ntype"},
    CropPft: {"npft", "ncpft", "ntype"},
    Nvg: {"nnvg", "ntype"},
}


def expected_names(dims: set[str]) -> set[str]:
    """Field names the given dimensions contribute, via an independent walk."""
    return {
        _strip_io(path.rsplit(".", 1)[1])
        for path, info in walk_fields(JulesNamelists)
        if (meta := find_list_len(info)) is not None and meta.dim in dims
    }


@pytest.mark.parametrize("model", [Pft, CropPft, Nvg])
def test_generated_model_covers_exactly_its_dims(model):
    """Every `ListLen` field of a group's dims is on its model, and no others.

    Set equality, not a subset check: this catches drift in both directions --
    a schema field the generator missed, and a stale field left behind after a
    schema field is removed or re-dimensioned.
    """
    assert set(model.model_fields) - {"name", "type"} == expected_names(DIMS_FOR[model])


def test_generated_models_are_not_empty():
    """Guard against a bug that empties both sides of the equality above."""
    assert len(Pft.model_fields) > 50
    assert {"canht_ft", "lai", "neff", "g_area", "rsurf_std"} <= set(Pft.model_fields)
    assert {"t_bse", "canht_ft"} <= set(CropPft.model_fields)
    assert {"albsnc_nvg", "rsurf_std"} <= set(Nvg.model_fields)


def test_groups_exclude_parameters_that_do_not_apply():
    """The split is structural: crop and TRIFFID parameters are not universal."""
    assert "t_bse" not in Pft.model_fields  # ncpft: crop PFTs only
    assert "g_area" not in CropPft.model_fields  # nnpft: natural PFTs only
    assert "canht_ft" not in Nvg.model_fields  # npft: vegetated only


def test_every_list_len_dim_belongs_to_a_group():
    """A new dimension added to `LIST_LEN_DIMS` must be assigned to a group."""
    assert set(CONTRIBUTORS) == set(LIST_LEN_DIMS)


def test_every_surface_type_member_is_classified():
    """A new `jules_surface_types` member must be classified veg / non-veg."""
    classified = VEG_TYPE_IDS | NVG_TYPE_IDS | SHARED_TYPE_IDS
    assert classified | {"npft", "nnvg", "ncpft"} == set(JulesSurfaceTypes.model_fields)


def test_io_stripping_is_collision_free():
    """Q7: stripping `_io` must not merge two distinct parameters."""
    names = [
        _strip_io(path.rsplit(".", 1)[1])
        for path, info in walk_fields(JulesNamelists)
        if find_list_len(info) is not None
    ]
    assert len(names) == len(set(names))
    assert "name" not in names
    assert "type" not in names


@pytest.mark.parametrize("model", [Pft, CropPft, Nvg])
def test_generated_fields_default_to_none(model):
    """A generated field must never carry a scalar default.

    A default here would silently give *every* surface type a value the user
    never wrote, breaking the rule that julesconf omits what it has no value
    for.
    """
    for name, info in model.model_fields.items():
        assert info.default is None, name


def test_bounds_carry_over_from_the_flat_schema():
    """Constrained element types must still be enforced on the generated model."""
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        Pft.model_validate({"albsnc_max": 5.0})  # a Fraction, so <= 1.0


def test_sentinel_validators_carry_over():
    """`SentinelOrFraction` keeps working on the generated model."""
    assert Nvg.model_validate({"albsnf_nvg": -1.0}).model_dump()["albsnf_nvg"] == -1.0
    with pytest.raises(ValidationError, match="sentinel"):
        Nvg.model_validate({"albsnf_nvg": 1.5})


def test_field_documentation_carries_over():
    """Generation is only worthwhile if the docs come with it."""
    assert Pft.model_fields["canht_ft"].description
    assert "canopy height" in Pft.model_fields["canht_ft"].description
