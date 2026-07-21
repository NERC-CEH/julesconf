"""Validation schema for `fire.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/fire.nml.rst`
"""

from julesconf.schemas._base import NamelistModel

__all__ = ["FireNamelist"]


class FireSwitches(NamelistModel):
    """`FIRE_SWITCHES` namelist members."""

    l_fire: bool = False
    """Switch to enable the fire module."""


class FireNamelist(NamelistModel):
    """Top-level schema for `fire.nml`."""

    fire_switches: FireSwitches = FireSwitches()
