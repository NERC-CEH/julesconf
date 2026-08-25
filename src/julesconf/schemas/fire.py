"""Validation schema for `fire.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/fire.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import name_or_value

__all__ = ["FireNamelist", "FireSwitches", "McArthurOpt"]


class McArthurOpt(IntEnum):
    """Soil moisture deficit method for the McArthur FFDI (`mcarthur_opt`)."""

    model_soil_moisture = 1
    fixed_120mm = 2


class FireSwitches(NamelistModel):
    """`FIRE_SWITCHES` namelist members."""

    l_fire: bool = False
    """Switch to enable the fire module."""
    mcarthur_flag: bool = False
    """Switch for calculating the McArthur Forest Fire Danger Index (FFDI)."""
    mcarthur_opt: Annotated[McArthurOpt, name_or_value(McArthurOpt)] = (
        McArthurOpt.model_soil_moisture
    )
    """Soil moisture deficit method for the McArthur FFDI.

    `model_soil_moisture` (1) uses the model soil moisture; `fixed_120mm` (2)
    uses a fixed value of 120 mm.
    """
    canadian_flag: bool = False
    """Switch for calculating the Canadian Fire Weather Index (FWI)."""
    canadian_hemi_opt: bool = False
    """Offset the month-dependent FWI parameters by 6 months in the S hemisphere.

    This causes a discontinuity in results when crossing the equator.
    """
    nesterov_flag: bool = False
    """Switch for calculating the Nesterov Index."""


class FireNamelist(NamelistModel):
    """Top-level schema for `fire.nml`."""

    fire_switches: FireSwitches = FireSwitches()
