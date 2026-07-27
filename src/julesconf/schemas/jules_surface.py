"""Validation schema for `jules_surface.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import warn_inactive
from julesconf.schemas.constraints import name_or_value

__all__ = [
    "FdHillOption",
    "FdStabilityDep",
    "FormDrag",
    "IModiscOpt",
    "JulesSurface",
    "JulesSurfaceNamelist",
    "SrfExCnvGust",
]


class FormDrag(IntEnum):
    """Orographic form drag option (`formdrag`)."""

    no_orographic_stress = 0
    effective_roughness = 1
    distributed_drag = 2


class FdHillOption(IntEnum):
    """Orographic form drag formulation (`fd_hill_option`)."""

    steep_hill = 0
    low_hill = 1
    capped_low_hill = 2


class FdStabilityDep(IntEnum):
    """Stability dependence option for orographic form drag (`fd_stability_dep`)."""

    off = 0
    surface_ri = 1
    bulk_ri = 2


class IModiscOpt(IntEnum):
    """Method of discretisation in the surface layer (`i_modiscopt`)."""

    off = 0
    on = 1


class SrfExCnvGust(IntEnum):
    """Effect of convective downdraughts on surface exchange (`srf_ex_cnv_gust`)."""

    off = 0
    on = 1


class JulesSurface(NamelistModel):
    """`JULES_SURFACE` namelist members."""

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

    # --- Options with no effect in JULES standalone ---
    # Each of these is documented "NOT AVAILABLE TO STANDALONE" and carries a
    # rose `fail-if` requiring a non-standalone parent; they are modelled so a
    # UM-derived configuration round-trips, and default to the inactive value.
    formdrag: Annotated[FormDrag, name_or_value(FormDrag)] = (
        FormDrag.no_orographic_stress
    )
    """Orographic form drag option: `no_orographic_stress` (0), `effective_roughness` (1), `distributed_drag` (2)."""
    fd_hill_option: Annotated[FdHillOption, name_or_value(FdHillOption)] = (
        FdHillOption.steep_hill
    )
    """Orographic form drag formulation: `steep_hill` (0), `low_hill` (1), `capped_low_hill` (2). Only used with `formdrag` = `distributed_drag`."""
    fd_stability_dep: Annotated[FdStabilityDep, name_or_value(FdStabilityDep)] = (
        FdStabilityDep.off
    )
    """Stability dependence of the orographic form drag: `off` (0), `surface_ri` (1), `bulk_ri` (2)."""
    orog_drag_param: float | None = Field(default=None, ge=0.01, le=10.0)
    """Drag coefficient for orographic form drag. Only used when `formdrag` is not `no_orographic_stress`."""
    i_modiscopt: Annotated[IModiscOpt, name_or_value(IModiscOpt)] = IModiscOpt.off
    """Method of discretisation in the surface layer: `off` (0), `on` (1)."""
    srf_ex_cnv_gust: Annotated[SrfExCnvGust, name_or_value(SrfExCnvGust)] = (
        SrfExCnvGust.off
    )
    """Include the effect of convective downdraughts on surface exchange: `off` (0), `on` (1)."""
    l_vary_z0m_soil: bool = False
    """Set the soil roughness from an ancillary file."""

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesSurface":
        """`i_aggregate_opt` is only read when tiles are aggregated."""
        if not self.l_aggregate:
            warn_inactive(self, ("i_aggregate_opt",), because="l_aggregate is false")
        if self.formdrag == FormDrag.no_orographic_stress:
            warn_inactive(
                self,
                ("orog_drag_param", "fd_stability_dep", "fd_hill_option"),
                because="formdrag is no_orographic_stress",
            )
        elif self.formdrag != FormDrag.distributed_drag:
            warn_inactive(
                self, ("fd_hill_option",), because="formdrag is not distributed_drag"
            )
        return self


class JulesSurfaceNamelist(NamelistModel):
    """Top-level schema for `jules_surface.nml`."""

    jules_surface: JulesSurface
