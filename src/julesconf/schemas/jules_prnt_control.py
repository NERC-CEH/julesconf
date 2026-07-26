"""Validation schema for `jules_prnt_control.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_prnt_control.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import name_or_value

__all__ = ["JulesPrntControl", "JulesPrntControlNamelist", "PrntWriters"]


class PrntWriters(IntEnum):
    """Which tasks of a parallel job write informative output (`prnt_writers`)."""

    master_only = 1
    all_tasks = 2


class JulesPrntControl(NamelistModel):
    """`JULES_PRNT_CONTROL` namelist members."""

    print_step: int = 1
    """Number of timesteps between printing timestep information to screen."""
    prnt_writers: Annotated[PrntWriters, name_or_value(PrntWriters)] = (
        PrntWriters.master_only
    )
    """Selects which tasks in a parallel job write informative output."""


class JulesPrntControlNamelist(NamelistModel):
    """Top-level schema for `jules_prnt_control.nml`."""

    jules_prnt_control: JulesPrntControl = JulesPrntControl()
