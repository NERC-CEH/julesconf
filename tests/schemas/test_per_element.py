"""Gates for `PerElementDefault` expansion.

Fortran namelist input does not broadcast a scalar across an array, so a
documented default of "T for every element" must be written out in full.
See the "Test suite" section of `notes/toml_config.md`.
"""

import re

import pytest
from conftest import flatten, minimal_valid

from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists
from julesconf.schemas._base import NamelistModel
from julesconf.schemas._namelists import find_per_element_default
from julesconf.schemas.constraints import (
    PER_ELEMENT_DIMS,
    SIBLING_DIMS,
    PerElementDefault,
)

REFERENCE = "reference/jules-lsm.github.io/user_guide/doc/source/namelists"


def _expanded(config) -> dict:
    """Return the flattened dict that would be written to namelists.

    Asserted against directly rather than via a written file: Fortran cannot
    distinguish a one-element array from a scalar, so `f90nml` reads
    `use_file = T` back as a bool regardless of what was written.
    `test_single_element_lists_survive_a_file_round_trip` covers that path.
    """
    return flatten(JulesNamelists.model_validate(config).to_namelist_dict())


# ---------------------------------------------------------------------------
# P1 / P2 / P3 -- sibling (nvars) dimensions
# ---------------------------------------------------------------------------


def test_expands_to_nvars_copies():
    """An unset per-element field is written once per variable."""
    config = minimal_valid()
    config["ancillaries"] = {
        "jules_soil_props": {"nvars": 3, "var": ["b", "sathh", "satcon"]}
    }
    written = _expanded(config)

    assert written["ancillaries.jules_soil_props.use_file"] == [True, True, True]
    assert written["ancillaries.jules_soil_props.var_name"] == ["", "", ""]


def test_zero_dimension_omits_the_member():
    """nvars = 0 means the block is inactive; an empty assignment is invalid."""
    config = minimal_valid()
    config["ancillaries"] = {"jules_soil_props": {"nvars": 0}}
    written = _expanded(config)

    assert "ancillaries.jules_soil_props.use_file" not in written
    assert "ancillaries.jules_soil_props.var_name" not in written


def test_explicit_value_is_not_overwritten():
    """A user-supplied list survives untouched -- no padding, no replacement."""
    config = minimal_valid()
    config["ancillaries"] = {
        "jules_soil_props": {
            "nvars": 3,
            "var": ["b", "sathh", "satcon"],
            "use_file": [False, True, False],
        }
    }
    written = _expanded(config)

    assert written["ancillaries.jules_soil_props.use_file"] == [False, True, False]


def test_expansion_respects_each_blocks_own_nvars():
    """Sibling dims are per-block, not global."""
    config = minimal_valid()
    config["ancillaries"] = {
        "jules_soil_props": {"nvars": 3, "var": ["b", "sathh", "satcon"]},
        "jules_top": {"nvars": 1, "var": ["fexp"]},
    }
    written = _expanded(config)

    assert len(written["ancillaries.jules_soil_props.use_file"]) == 3
    assert len(written["ancillaries.jules_top.use_file"]) == 1


# ---------------------------------------------------------------------------
# P4 -- global dimensions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("npft", [1, 5, 9])
def test_expands_to_npft_copies(npft):
    """cansnowpft is dimensioned by the global npft, not a sibling field."""
    written = _expanded(minimal_valid(npft=npft))
    assert written["jules_snow.jules_snow.cansnowpft"] == [False] * npft


def test_single_element_lists_survive_a_file_round_trip(tmp_path):
    """A one-element array is written as a scalar, and must still re-validate.

    Fortran cannot distinguish `use_file = T` from a scalar assignment, so
    `f90nml` reads a one-element array back as a bool. `NamelistModel` coerces
    it back to a list; without that, no single-PFT config could be read at all.
    """
    config = minimal_valid(npft=1)
    config["ancillaries"] = {"jules_top": {"nvars": 1, "var": ["fexp"]}}
    JulesNamelists.model_validate(config).to_namelists(tmp_path, overwrite_ok=True)

    raw = flatten(NamelistConfig().read(tmp_path))
    assert raw["jules_snow.jules_snow.cansnowpft"] is False  # collapsed by Fortran

    model = JulesNamelists.from_namelists(tmp_path)
    assert model.jules_snow.jules_snow.cansnowpft == [False]
    assert model.ancillaries.jules_top.use_file == [True]


# ---------------------------------------------------------------------------
# P5 -- TOML stays terse
# ---------------------------------------------------------------------------


def test_toml_does_not_expand(tmp_path):
    """Expansion is a write-time concern; the user's TOML stays readable."""
    config = minimal_valid()
    config["ancillaries"] = {
        "jules_soil_props": {"nvars": 3, "var": ["b", "sathh", "satcon"]}
    }
    model = JulesNamelists.model_validate(config)

    assert "use_file" not in model.to_toml_dict()["ancillaries"]["jules_soil_props"]
    assert "cansnowpft" not in model.to_toml_dict()["jules_snow"]["jules_snow"]

    path = tmp_path / "c.toml"
    model.to_toml(path)
    assert "use_file" not in path.read_text()


# ---------------------------------------------------------------------------
# P6 -- anti-drift: the marker must keep covering what the reference documents
# ---------------------------------------------------------------------------


def _iter_fields(model_cls, seen=None):
    """Yield (module, class, field_name, field_info) over the whole model tree."""
    seen = seen if seen is not None else set()
    if model_cls in seen:
        return
    seen.add(model_cls)
    for name, info in model_cls.model_fields.items():
        yield model_cls, name, info
        candidates = [info.annotation, *getattr(info.annotation, "__args__", ())]
        for candidate in candidates:
            if isinstance(candidate, type) and issubclass(candidate, NamelistModel):
                yield from _iter_fields(candidate, seen)


def _documented_per_element_defaults() -> dict[str, str]:
    """Map member name -> documented default, for list-typed members with one.

    Scans only the namelists julesconf schemas. Globbing every `*.nml.rst`
    would pull in the postponed namelists (`cable_*`, `oasis_rivers`,
    `red_params`), whose members julesconf deliberately does not model.
    """
    import pathlib

    schema_dir = pathlib.Path("src/julesconf/schemas")
    modules = [
        p.stem
        for p in schema_dir.glob("*.py")
        if not p.stem.startswith("_") and p.stem != "constraints"
    ]

    found = {}
    for module in modules:
        path = pathlib.Path(REFERENCE) / f"{module}.nml.rst"
        if not path.is_file():
            continue
        text = path.read_text()
        for name, body in re.findall(
            r"nml:member:: *([a-zA-Z0-9_]+)(.*?)(?=nml:member::|\Z)", text, re.S
        ):
            type_match = re.search(r":type: *(.*)", body)
            default_match = re.search(r":default: *(.*)", body)
            if not type_match or not default_match:
                continue
            type_str, default = (
                type_match.group(1).strip(),
                default_match.group(1).strip(),
            )
            # Only a *named* dimension marks a runtime-sized array. A literal
            # one -- `real(3)`, `character(1)` -- is either a fixed-length array
            # (whose default is the full tuple, so an ordinary Pydantic default
            # suffices) or a Fortran string length, which is not an array at all.
            dim = re.search(r"\(([^)]*)\)", type_str)
            if dim is None or dim.group(1).strip().isdigit():
                continue
            if default.lower() not in ("", "none", "none.", "mdi"):
                found[name] = default
    return found


def test_every_marked_field_uses_a_resolvable_dim():
    """A PerElementDefault dim must be resolvable, globally or from a sibling."""
    for model_cls, name, info in _iter_fields(JulesNamelists):
        meta = find_per_element_default(info)
        if meta is None:
            continue
        assert meta.dim in PER_ELEMENT_DIMS, f"{model_cls.__name__}.{name}"
        if meta.dim in SIBLING_DIMS:
            assert meta.dim in model_cls.model_fields, (
                f"{model_cls.__name__}.{name} declares sibling dim {meta.dim!r}"
                f" but {model_cls.__name__} has no such field"
            )


def test_marker_covers_the_documented_per_element_defaults():
    """Anti-drift: a documented per-element default must carry the marker.

    Without this, adding a schema field with a documented per-element default
    would silently omit it from written namelists -- the exact failure this
    machinery exists to prevent.
    """
    documented = _documented_per_element_defaults()

    marked = set()
    unmarked = set()
    for _model_cls, name, info in _iter_fields(JulesNamelists):
        if name not in documented:
            continue
        if find_per_element_default(info) is not None:
            marked.add(name)
        else:
            unmarked.add(name)

    # `const_val` appears in 11 blocks; only JULES_FLAKE documents a default
    # (5.0 m lake depth), and only JulesFlake overrides it. The other 10 inherit
    # the unmarked `_NvarsModel.const_val`, which is correct. This lookup is
    # keyed by member name alone, so it cannot tell those cases apart.
    exclusions = {"const_val"}
    missing = unmarked - marked - exclusions
    assert not missing, (
        f"fields with a documented per-element default but no PerElementDefault"
        f" marker: {sorted(missing)}"
    )


def test_marker_rejects_unknown_dim():
    """A typo'd dimension fails loudly at import time, not silently at write time."""
    with pytest.raises(ValueError, match="Unknown PerElementDefault dim"):
        PerElementDefault(True, "nsurfacetypes")
