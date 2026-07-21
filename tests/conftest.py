"""Shared fixtures for the julesconf test suite."""

import pytest


def minimal_valid(npft: int = 5, nnvg: int = 4, ncpft: int = 0) -> dict:
    """Return the smallest dict that validates as a JulesNamelists.

    Only the namelists without defaults are populated. Tests that need a
    particular namelist add it themselves.

    Args:
        npft: Number of plant functional types.
        nnvg: Number of non-vegetated surface types.
        ncpft: Number of crop plant functional types.

    Returns:
        A dict suitable for `JulesNamelists.model_validate`.
    """
    return {
        "drive": {"jules_drive": {}},
        "initial_conditions": {"jules_initial": {}},
        "jules_hydrology": {"jules_hydrology": {}},
        "jules_radiation": {"jules_radiation": {}},
        "jules_soil": {"jules_soil": {}},
        "jules_surface": {"jules_surface": {}},
        "jules_surface_types": {
            "jules_surface_types": {"npft": npft, "nnvg": nnvg, "ncpft": ncpft}
        },
        "jules_vegetation": {"jules_vegetation": {}},
        "model_environment": {"jules_model_environment": {}},
        "nveg_params": {"jules_nvegparm": {}},
        "pft_params": {"jules_pftparm": {}},
        "timesteps": {
            "jules_time": {
                "timestep_len": 1800,
                "main_run_start": "1997-01-01 00:00:00",
                "main_run_end": "1998-01-01 00:00:00",
            }
        },
    }


@pytest.fixture
def minimal_config() -> dict:
    """A minimal valid JulesNamelists dict."""
    return minimal_valid()


def minimal_grouped(n_pft: int = 2, n_crop: int = 0, n_nvg: int = 2) -> dict:
    """Return a minimal valid config in the grouped form.

    The `jules_surface_types`, `pft_params` and `nveg_params` tables are
    replaced by the arrays of tables that derive them.

    Args:
        n_pft: Number of natural PFT entries.
        n_crop: Number of crop PFT entries.
        n_nvg: Number of non-vegetated entries.

    Returns:
        A dict suitable for `JulesNamelists.from_toml`'s grouped path.
    """
    data = minimal_valid()
    for key in ("jules_surface_types", "pft_params", "nveg_params"):
        del data[key]

    veg = ["brd_leaf", "ndl_leaf", "c3_grass", "c4_grass", "shrub"]
    nvg = ["urban", "lake", "soil", "ice"]

    def entries(names: list[str], count: int, offset: int = 0) -> list[dict]:
        # A surface type identifier is optional, and there are only so many;
        # entries beyond the supply simply go untyped.
        return [
            {"type": names[offset + i]} if offset + i < len(names) else {}
            for i in range(count)
        ]

    data["pft"] = entries(veg, n_pft)
    if n_crop:
        data["crop_pft"] = entries(veg, n_crop, offset=n_pft)
    data["nvg"] = entries(nvg, n_nvg)
    return data


def walk_fields(model, path=()):
    """Walk a model tree yielding `(dotted_path, field_info)` for leaf fields.

    Deliberately a second implementation of `julesconf.schemas._base.
    iter_leaf_fields`. The grouped models are generated from that traversal, so
    a test that reused it could not detect a bug in it.
    """
    from julesconf.schemas._base import NamelistModel

    for name, info in model.model_fields.items():
        annotation = info.annotation
        if isinstance(annotation, type) and issubclass(annotation, NamelistModel):
            yield from walk_fields(annotation, (*path, name))
        else:
            yield ".".join((*path, name)), info


def flatten(data: dict) -> dict:
    """Flatten a `{namelist: {block: {member: value}}}` dict to dotted keys.

    Args:
        data: A nested namelist dict.

    Returns:
        A flat `{"namelist.block.member": value}` dict.
    """
    out = {}
    for filename, blocks in data.items():
        for block, members in (blocks or {}).items():
            if isinstance(members, dict):
                for key, value in members.items():
                    out[f"{filename}.{block}.{key}"] = value
    return out


def assert_superset(original: dict, written: dict) -> None:
    """Assert a written config preserves everything in the original.

    Writing namelists is deliberately not the inverse of reading them: julesconf
    inserts every default it holds, so the output is a *superset* of the input.
    Asserting equality here would fail for the right reason and invite being
    weakened; this checks the property that actually matters.

    Args:
        original: The namelist dict that was read.
        written: The namelist dict that was written back.

    Raises:
        AssertionError: If a member was lost or its value changed.
    """
    src, dst = flatten(original), flatten(written)

    missing = sorted(set(src) - set(dst))
    assert not missing, f"members lost when writing: {missing}"

    changed = {k: (src[k], dst[k]) for k in src if src[k] != dst[k]}
    assert not changed, f"members changed when writing: {changed}"
