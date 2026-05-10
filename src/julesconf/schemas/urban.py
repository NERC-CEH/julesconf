"""Validation schema for ``urban.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/urban.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["UrbanNamelist"]


class JulesUrban(BaseModel):
    """``JULES_URBAN`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    anthrop_heat_scale: float = Field(default=1.0, ge=0.0, le=1.0)
    """Distribution scaling factor for anthropogenic heat flux spread between urban_canyon and urban_roof surface tiles."""
    l_moruses_albedo: bool = False
    """Switch to use MORUSES parameterisation for effective canyon albedo (snow-free), including shading and multiple reflections."""
    l_moruses_emissivity: bool = False
    """Switch to use MORUSES parameterisation for effective canyon emissivity, accounting for multiple reflections."""
    l_moruses_rough: bool = False
    """Switch to use MORUSES parameterisation for effective roughness length for heat, based on canyon geometry and flow regimes."""
    l_moruses_storage: bool = False
    """Switch to use MORUSES parameterisation for thermal inertia and soil coupling; modifies coupling definitions for roof surfaces."""
    l_moruses_storage_thin: bool = False
    """Switch to use a thin, insulated roof to simulate insulation effects (only if ``l_moruses_storage`` = TRUE)."""
    l_moruses_macdonald: bool = False
    """Switch to use MacDonald et al. (1998) formulations for roughness length and displacement height from urban geometry."""
    l_urban_empirical: bool = False
    """Switch to use empirical relationships for urban geometry (W/R, H/W, H) based on total urban fraction."""


class UrbanNamelist(BaseModel):
    """Top-level schema for ``urban.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_urban: JulesUrban = JulesUrban()
