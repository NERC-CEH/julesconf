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
