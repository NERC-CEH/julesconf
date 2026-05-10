"""Validation schema for ``jules_prnt_control.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_prnt_control.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["JulesPrntControlNamelist"]


class JulesPrntControl(BaseModel):
    """``JULES_PRNT_CONTROL`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    print_step: int = 1
    """Number of timesteps between printing timestep information to screen."""


class JulesPrntControlNamelist(BaseModel):
    """Top-level schema for ``jules_prnt_control.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_prnt_control: JulesPrntControl = JulesPrntControl()
