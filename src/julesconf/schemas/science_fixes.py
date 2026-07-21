"""Validation schema for `science_fixes.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/science_fixes.nml.rst`
"""

from pydantic import Field

from julesconf.schemas._base import NamelistModel

__all__ = ["JulesTempFixes", "ScienceFixesNamelist"]


class JulesTempFixes(NamelistModel):
    """`JULES_TEMP_FIXES` namelist members."""

    ctile_orog_fix: int = Field(default=2, ge=0, le=2)
    """Corrects surface exchange calculations in coastally tiled grid-boxes."""
    l_accurate_rho: bool = False
    """Improves the calculation of surface air density in the surface turbulent fluxes."""
    l_dtcanfix: bool = False
    """Corrects a bug in the evolution of the skin temperature in the implicit solver."""
    l_fix_alb_ice_thick: bool = False
    """Removes the effective thickness adjustment when multi-layer sea ice is used."""
    l_fix_albsnow_ts: bool = False
    """Applies the appropriate correction to a bug in the two-stream scheme's albedo calculation."""
    l_fix_drydep_so2_water: bool = False
    """Corrects the surface resistance of SO2 to water when calculating dry deposition."""
    l_fix_improve_drydep: bool = False
    """Makes the surface resistance terms for the 9-tile configuration consistent with others."""
    l_fix_lake_ice_temperatures: bool = False
    """Allows sea ice temperatures in lakes to evolve over time for coupled models."""
    l_fix_moruses_roof_rad_coupling: bool = False
    """Corrects a bug in the surface energy balance when MORUSES radiative roof coupling is used."""
    l_fix_neg_snow: bool = False
    """Corrects formulations of melting, interception and unloading that may result in negative snow."""
    l_fix_osa_chloro: bool = False
    """Corrects chlorophyll content units from gm⁻³ to mg m⁻³ for ocean surface albedo calculations."""
    l_fix_snow_frac: bool = False
    """Corrects issues with snow mass persistence and potential evaporation calculations."""
    l_fix_ukca_h2dd_x: bool = False
    """Corrects a bug in the elements of h2dd_c and h2dd_m used for H2 dry deposition calculation."""
    l_fix_ustar_dust: bool = False
    """Corrects how ustar is calculated in the exchange coefficient for dust deposition."""
    l_fix_wind_snow: bool = False
    """Ensures that wind speed is calculated for use in snow unloading."""


class ScienceFixesNamelist(NamelistModel):
    """Top-level schema for `science_fixes.nml`."""

    jules_temp_fixes: JulesTempFixes = JulesTempFixes()
