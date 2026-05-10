"""Validation schema for ``jules_irrig.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_irrig.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["JulesIrrigNamelist"]


class JulesIrrig(BaseModel):
    """``JULES_IRRIG`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_irrig_dmd: bool = False
    l_irrig_limit: bool = False


class JulesIrrigNamelist(BaseModel):
    """Top-level schema for ``jules_irrig.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_irrig: JulesIrrig = JulesIrrig()
