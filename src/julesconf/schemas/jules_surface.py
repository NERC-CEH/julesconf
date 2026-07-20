"""Validation schema for ``jules_surface.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface.nml.rst``
"""

from pydantic import Field

from julesconf.schemas._base import NamelistModel

__all__ = ["JulesSurfaceNamelist"]


class JulesSurface(NamelistModel):
    """``JULES_SURFACE`` namelist members."""

    all_tiles: int = Field(default=0, ge=0, le=1)
    """Perform calculations on all tiles for all gridpoints even when the tile fraction is zero."""
    cor_mo_iter: int = Field(default=1, ge=1, le=4)
    """Corrections to Monin-Obukhov surface exchange calculation."""
    i_aggregate_opt: int = Field(default=0, ge=0, le=1)
    """Option for aggregating surface properties to surface tiles."""
    iscrntdiag: int = Field(default=0, ge=0, le=3)
    """Switch controlling method for diagnosing screen temperature."""
    anthrop_heat_option: int = Field(default=0, ge=0, le=1)
    l_aggregate: bool = False
    """Switch controlling number of surface tiles for each gridbox."""
    l_anthrop_heat_src: bool = False
    """Switch for inclusion of anthropogenic contribution to the surface heat flux from urban types."""
    l_elev_land_ice: bool = False
    """Allows multiple ice surface tiles at different elevations for sub-gridscale surface mass balance."""
    l_elev_lw_down: bool = False
    """Controls whether downwelling longwave radiation is adjusted with surface tile elevation offsets."""
    l_epot_corr: bool = False
    """Use correction to the calculation of potential evaporation."""
    l_flake_model: bool = False
    """Switch for using the freshwater lake model FLake on the lake/inland-water surface tile."""
    l_land_ice_imp: bool = False
    """Switch to control the use of implicit numerics to update land ice temperatures."""
    l_mo_buoyancy_calc: bool = False
    """Default JULES uses buoyancy from the previous timestep to calculate surface transfer coefficients."""
    l_point_data: bool = False
    """Flag indicating if driving data are point or area-average values."""
    l_urban2t: bool = False
    """Switch for using the two-tile urban schemes (including MORUSES)."""
    hleaf: float = 5.7e4
    """Specific heat capacity of leaves (J K⁻¹ per kg carbon)."""
    hwood: float = 1.1e4
    """Specific heat capacity of wood (J K⁻¹ per kg carbon)."""
    beta1: float = 0.83
    """Coupling coefficient for co-limitation in photosynthesis model."""
    beta2: float = 0.93
    """Coupling coefficient for co-limitation in photosynthesis model."""
    fwe_c3: float = 0.5
    """Constant in expression for limitation of photosynthesis by transport of products for C3 plants."""
    fwe_c4: float = 20000.0
    """Constant in expression for limitation of photosynthesis by transport of products for C4 plants."""
    anthrop_heat_mean: float = 20.0
    beta_cnv_bl: float | None = None
    """Dimensionless coefficient scaling boundary layer convective gustiness contribution."""


class JulesSurfaceNamelist(NamelistModel):
    """Top-level schema for ``jules_surface.nml``."""

    jules_surface: JulesSurface
