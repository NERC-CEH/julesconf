"""Validation schema for `jules_prnt_control.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_prnt_control.nml.rst`
"""

from julesconf.schemas._base import NamelistModel

__all__ = ["JulesPrntControlNamelist"]


class JulesPrntControl(NamelistModel):
    """`JULES_PRNT_CONTROL` namelist members."""

    print_step: int = 1
    """Number of timesteps between printing timestep information to screen."""


class JulesPrntControlNamelist(NamelistModel):
    """Top-level schema for `jules_prnt_control.nml`."""

    jules_prnt_control: JulesPrntControl = JulesPrntControl()
