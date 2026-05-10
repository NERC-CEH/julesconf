"""Validation schema for ``jules_surface.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["JulesSurfaceNamelist"]


class JulesSurface(BaseModel):
    """``JULES_SURFACE`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    all_tiles: int = Field(default=0, ge=0, le=1)
    cor_mo_iter: int = Field(default=1, ge=1, le=4)
    i_aggregate_opt: int = Field(default=0, ge=0, le=1)
    iscrntdiag: int = Field(default=0, ge=0, le=3)
    anthrop_heat_option: int = Field(default=0, ge=0, le=1)
    l_aggregate: bool = False
    l_anthrop_heat_src: bool = False
    l_elev_land_ice: bool = False
    l_elev_lw_down: bool = False
    l_epot_corr: bool = False
    l_flake_model: bool = False
    l_land_ice_imp: bool = False
    l_mo_buoyancy_calc: bool = False
    l_point_data: bool = False
    l_urban2t: bool = False
    hleaf: float = 5.7e4
    hwood: float = 1.1e4
    beta1: float = 0.83
    beta2: float = 0.93
    fwe_c3: float = 0.5
    fwe_c4: float = 20000.0
    anthrop_heat_mean: float = 20.0
    beta_cnv_bl: float | None = None


class JulesSurfaceNamelist(BaseModel):
    """Top-level schema for ``jules_surface.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_surface: JulesSurface
