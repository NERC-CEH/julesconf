"""Validation schema for ``jules_water_resources.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_water_resources.nml.rst``
"""

from typing import Literal

from pydantic import Field

from julesconf.schemas._base import NamelistModel

__all__ = ["JulesWaterResourcesNamelist"]


class JulesWaterResources(NamelistModel):
    """``JULES_WATER_RESOURCES`` namelist members."""

    l_water_resources: bool = False
    """Switch to enable modelling of water resources."""
    nstep_water_res: int | None = Field(default=None, ge=1)
    """Number of model timesteps per water resource timestep; must align with river routing calls."""
    l_water_domestic: bool = False
    """Switch to enable domestic water demand modelling; requires prescribed input data."""
    l_water_environment: bool = False
    """Switch to enable environmental flow requirement modelling."""
    l_water_industry: bool = False
    """Switch to enable industrial water demand modelling; requires prescribed input data."""
    l_water_irrigation: bool = False
    """Switch to enable irrigation demand; requires specific settings in JULES_IRRIG."""
    l_water_livestock: bool = False
    """Switch to enable livestock water demand modelling; requires prescribed input data."""
    l_water_transfers: bool = False
    """Switch to enable water transfer demand modelling; requires prescribed input data."""
    l_prioritise: bool = False
    """Switch controlling prioritisation of demands when water supply is insufficient."""
    priority: list[str] | None = None
    """List of water sector names in order of decreasing priority; all active sectors must be listed."""
    nr_gwater_model: Literal[0, 1, 2] | None = None
    """Non-renewable groundwater approach: 0 = none, 1 = last resort, 2 = mixed."""
    rf_domestic: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after domestic abstraction."""
    rf_industry: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after industrial abstraction."""
    rf_livestock: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after livestock abstraction."""


class JulesWaterResourcesNamelist(NamelistModel):
    """Top-level schema for ``jules_water_resources.nml``."""

    jules_water_resources: JulesWaterResources = JulesWaterResources()
