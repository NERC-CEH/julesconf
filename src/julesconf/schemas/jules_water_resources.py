"""Validation schema for ``jules_water_resources.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_water_resources.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["JulesWaterResourcesNamelist"]


class JulesWaterResources(BaseModel):
    """``JULES_WATER_RESOURCES`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_water_resources: bool = False


class JulesWaterResourcesNamelist(BaseModel):
    """Top-level schema for ``jules_water_resources.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_water_resources: JulesWaterResources = JulesWaterResources()
