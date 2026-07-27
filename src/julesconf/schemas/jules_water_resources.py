"""Validation schema for `jules_water_resources.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_water_resources.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import warn_inactive
from julesconf.schemas.constraints import name_or_value

__all__ = [
    "JulesWaterResources",
    "JulesWaterResourcesNamelist",
    "NrGwaterModel",
]


class NrGwaterModel(IntEnum):
    """Model for non-renewable groundwater (`nr_gwater_model`)."""

    none = 0
    last_resort = 1
    mix = 2


class JulesWaterResources(NamelistModel):
    """`JULES_WATER_RESOURCES` namelist members."""

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
    nr_gwater_model: Annotated[NrGwaterModel, name_or_value(NrGwaterModel)] | None = (
        None
    )
    """Non-renewable groundwater approach: `none` (0), `last_resort` (1, used only when no other source is available), `mix` (2, used alongside other sources)."""
    rf_domestic: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after domestic abstraction."""
    rf_industry: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after industrial abstraction."""
    rf_livestock: float | None = Field(default=None, ge=0, le=1)
    """Fraction of water returned to the system after livestock abstraction."""

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesWaterResources":
        """Every other member of the block is read only when water resources are on."""
        if not self.l_water_resources:
            warn_inactive(
                self,
                (
                    "l_prioritise",
                    "l_water_domestic",
                    "l_water_environment",
                    "l_water_industry",
                    "l_water_irrigation",
                    "l_water_livestock",
                    "l_water_transfers",
                    "nr_gwater_model",
                    "nstep_water_res",
                ),
                because="l_water_resources is false",
            )
        return self


class JulesWaterResourcesNamelist(NamelistModel):
    """Top-level schema for `jules_water_resources.nml`."""

    jules_water_resources: JulesWaterResources = JulesWaterResources()
