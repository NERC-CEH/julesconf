"""Validation schema for `imogen.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/imogen.nml.rst`
"""

from julesconf.schemas._base import NamelistModel

__all__ = ["ImogenNamelist"]


class ImogenOnoffSwitch(NamelistModel):
    """`IMOGEN_ONOFF_SWITCH` namelist members."""

    l_imogen: bool = False
    """Switch for IMOGEN."""


class ImogenRunList(NamelistModel):
    """`IMOGEN_RUN_LIST` namelist members."""


class ImogenAnlgValsList(NamelistModel):
    """`IMOGEN_ANLG_VALS_LIST` namelist members."""


class ImogenNamelist(NamelistModel):
    """Top-level schema for `imogen.nml`."""

    imogen_onoff_switch: ImogenOnoffSwitch = ImogenOnoffSwitch()
    imogen_run_list: ImogenRunList = ImogenRunList()
    imogen_anlg_vals_list: ImogenAnlgValsList = ImogenAnlgValsList()
