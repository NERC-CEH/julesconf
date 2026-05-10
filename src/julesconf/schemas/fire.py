"""Validation schema for ``fire.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/fire.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["FireNamelist"]


class FireSwitches(BaseModel):
    """``FIRE_SWITCHES`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_fire: bool = False


class FireNamelist(BaseModel):
    """Top-level schema for ``fire.nml``."""

    model_config = ConfigDict(extra="ignore")

    fire_switches: FireSwitches = FireSwitches()
