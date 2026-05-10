"""Validation schema for ``imogen.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/imogen.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["ImogenNamelist"]


class ImogenOnoffSwitch(BaseModel):
    """``IMOGEN_ONOFF_SWITCH`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_imogen: bool = False


class ImogenRunList(BaseModel):
    """``IMOGEN_RUN_LIST`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class ImogenAnlgValsList(BaseModel):
    """``IMOGEN_ANLG_VALS_LIST`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class ImogenNamelist(BaseModel):
    """Top-level schema for ``imogen.nml``."""

    model_config = ConfigDict(extra="ignore")

    imogen_onoff_switch: ImogenOnoffSwitch = ImogenOnoffSwitch()
    imogen_run_list: ImogenRunList = ImogenRunList()
    imogen_anlg_vals_list: ImogenAnlgValsList = ImogenAnlgValsList()
