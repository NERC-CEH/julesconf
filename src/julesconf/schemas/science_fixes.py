"""Validation schema for ``science_fixes.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/science_fixes.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ScienceFixesNamelist"]


class JulesTempFixes(BaseModel):
    """``JULES_TEMP_FIXES`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    ctile_orog_fix: int = Field(default=2, ge=0, le=2)
    l_accurate_rho: bool = False
    l_dtcanfix: bool = False
    l_fix_alb_ice_thick: bool = False
    l_fix_albsnow_ts: bool = False
    l_fix_drydep_so2_water: bool = False
    l_fix_improve_drydep: bool = False
    l_fix_lake_ice_temperatures: bool = False
    l_fix_moruses_roof_rad_coupling: bool = False
    l_fix_neg_snow: bool = False
    l_fix_osa_chloro: bool = False
    l_fix_snow_frac: bool = False
    l_fix_ukca_h2dd_x: bool = False
    l_fix_ustar_dust: bool = False
    l_fix_wind_snow: bool = False


class ScienceFixesNamelist(BaseModel):
    """Top-level schema for ``science_fixes.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_temp_fixes: JulesTempFixes = JulesTempFixes()
