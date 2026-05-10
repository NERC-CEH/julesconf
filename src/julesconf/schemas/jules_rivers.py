"""Validation schema for ``jules_rivers.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_rivers.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["JulesRiversNamelist"]


class JulesRivers(BaseModel):
    """``JULES_RIVERS`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_rivers: bool = False


class JulesOverbank(BaseModel):
    """``JULES_OVERBANK`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_riv_overbank: bool = False


class JulesRiversNamelist(BaseModel):
    """Top-level schema for ``jules_rivers.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_rivers: JulesRivers = JulesRivers()
    jules_overbank: JulesOverbank = JulesOverbank()
