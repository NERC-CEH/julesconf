"""Validation schema for `science_fixes.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/science_fixes.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import name_or_value

__all__ = ["CtileOrogFix", "JulesTempFixes", "ScienceFixesNamelist"]


class CtileOrogFix(IntEnum):
    """Surface exchange fix in coastally tiled grid-boxes (`ctile_orog_fix`)."""

    no_fix = 0
    correct_sea_adjust_land = 1
    correct_sea_only = 2


class JulesTempFixes(NamelistModel):
    """`JULES_TEMP_FIXES` namelist members.

    Each member enables a correction to a known JULES bug. They are switches
    rather than unconditional fixes because the UM and coupled configurations
    need to reproduce historical runs; standalone JULES does not.

    Seven of them carry a rose `fail-if` rule of the form "this should be
    `.true.` in JULES standalone", and julesconf defaults those seven to the
    corrected behaviour: `ctile_orog_fix` to `2` and the six booleans
    `l_dtcanfix`, `l_fix_alb_ice_thick`, `l_fix_albsnow_ts`, `l_fix_neg_snow`,
    `l_fix_ustar_dust` and `l_fix_wind_snow` to `True`. All 57 shipped JULES
    configurations that set them do the same.

    That choice matters more here than it would elsewhere, because julesconf
    writes every default explicitly: a `False` default would not be a neutral
    absence, it would emit `l_dtcanfix=.false.` and actively switch off a fix
    the model's authors say standalone runs should have on.

    The remaining members default to `False`, matching JULES. They are either
    specific to the UM, to UKCA, or to configurations julesconf does not model,
    and upstream states no standalone expectation for them.
    """

    ctile_orog_fix: Annotated[CtileOrogFix, name_or_value(CtileOrogFix)] = (
        CtileOrogFix.correct_sea_only
    )
    """Corrects surface exchange calculations in coastally tiled grid-boxes: `no_fix` (0), `correct_sea_adjust_land` (1), `correct_sea_only` (2)."""
    l_accurate_rho: bool = False
    """Improves the calculation of surface air density in the surface turbulent fluxes."""
    l_dtcanfix: bool = True
    """Corrects a bug in the evolution of the skin temperature in the implicit solver."""
    l_fix_alb_ice_thick: bool = True
    """Removes the effective thickness adjustment when multi-layer sea ice is used."""
    l_fix_albsnow_ts: bool = True
    """Applies the appropriate correction to a bug in the two-stream scheme's albedo calculation."""
    l_fix_drydep_so2_water: bool = False
    """Corrects the surface resistance of SO2 to water when calculating dry deposition."""
    l_fix_improve_drydep: bool = False
    """Makes the surface resistance terms for the 9-tile configuration consistent with others."""
    l_fix_lake_ice_temperatures: bool = False
    """Allows sea ice temperatures in lakes to evolve over time for coupled models."""
    l_fix_moruses_roof_rad_coupling: bool = False
    """Corrects a bug in the surface energy balance when MORUSES radiative roof coupling is used."""
    l_fix_neg_snow: bool = True
    """Corrects formulations of melting, interception and unloading that may result in negative snow."""
    l_fix_osa_chloro: bool = False
    """Corrects chlorophyll content units from gm⁻³ to mg m⁻³ for ocean surface albedo calculations."""
    l_fix_snow_frac: bool = False
    """Corrects issues with snow mass persistence and potential evaporation calculations."""
    l_fix_ukca_h2dd_x: bool = False
    """Corrects a bug in the elements of h2dd_c and h2dd_m used for H2 dry deposition calculation."""
    l_fix_ustar_dust: bool = True
    """Corrects how ustar is calculated in the exchange coefficient for dust deposition."""
    l_fix_wind_snow: bool = True
    """Ensures that wind speed is calculated for use in snow unloading."""


class ScienceFixesNamelist(NamelistModel):
    """Top-level schema for `science_fixes.nml`."""

    jules_temp_fixes: JulesTempFixes = JulesTempFixes()
