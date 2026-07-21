"""Validation schema for `jules_snow.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_snow.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import ListLen

__all__ = ["JulesSnow", "JulesSnowNamelist"]


class JulesSnow(NamelistModel):
    """`JULES_SNOW` namelist members."""

    nsmax: int = Field(default=0, ge=0)
    """Maximum possible number of snow layers."""
    l_snowdep_surf: bool = False
    """Use equivalent canopy snow depth for surface calculations on snow canopy tiles."""
    frac_snow_subl_melt: int = Field(default=0, ge=0, le=1)
    """Switch for use of snow-cover fraction in the calculation of sublimation and melting."""
    graupel_options: int = Field(default=0, ge=0, le=2)
    """Switch for treatment of graupel in the snow scheme."""

    # Length nsmax (only used if nsmax > 0)
    dzsnow: list[float] | None = None
    """Prescribed thickness of each snow layer (m)."""

    # Length npft (cross-namelist — validated in JulesNamelists)
    cansnowpft: Annotated[list[bool] | None, ListLen("npft")] = None
    """Flag indicating whether snow can be held under the canopy of each PFT."""

    # Radiation parameters
    r0: float = 50.0
    """Grain size for fresh snow (μm)."""
    rmax: float = 2000.0
    """Maximum snow grain size (μm)."""
    snow_ggr: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Snow grain area growth rates (μm² s⁻¹)."""
    amax: Annotated[list[float], Field(min_length=2, max_length=2)] | None = None
    """Maximum albedo for fresh snow."""
    aicemax: Annotated[list[float], Field(min_length=2, max_length=2)] | None = None
    """Maximum albedo for bare ice."""
    maskd: float = 50.0
    """Weighting factor for snow in overall surface albedo calculation based on e-folding depth."""
    dtland: float = 2.0
    """Degrees Celsius below zero at which snow albedo equals cold deep snow albedo."""
    kland_numerator: float = 0.3
    """Used in snow-ageing effect on albedo."""
    can_clump: Annotated[list[float] | None, ListLen("npft")] = None
    """Clumping parameter for snow on the canopy in calculation of albedo."""
    n_lai_exposed: Annotated[list[float] | None, ListLen("npft")] = None
    """LAI distribution parameter for calculation of snow albedo."""
    lai_alb_lim_sn: Annotated[list[float] | None, ListLen("npft")] = None
    """Minimum LAI in calculation of albedo in the presence of snow."""

    # Other snow parameters
    rho_snow_const: float = 250.0
    """Constant density of lying snow (kg m⁻³)."""
    rho_snow_fresh: float = 100.0
    """Density of fresh snow (kg m⁻³)."""
    rho_firn_albedo: float = 550.0
    """Threshold density at which grain-size albedo switches to density-dependent scheme."""
    snow_hcon: float = 0.265
    """Thermal conductivity of lying snow (W m⁻¹ K⁻¹)."""
    snow_hcap: float = 0.63e6
    """Thermal capacity of lying snow (J K⁻¹ m⁻³)."""
    snowliqcap: float = 0.05
    """Liquid water holding capacity of lying snow, as a fraction of snow mass."""
    snowinterceptfact: float = 0.7
    """Constant in relationship between mass of intercepted snow and snowfall rate."""
    snowloadlai: float = 4.4
    """Ratio of maximum canopy snow load to leaf area index (kg m⁻²)."""
    snowunloadfact: float = 0.4
    """Constant in relationship between canopy snow unloading and canopy snow melt rate."""
    unload_rate_cnst: Annotated[list[float] | None, ListLen("npft")] = None
    """Constant term in the background unloading rate for snow on the canopy."""
    unload_rate_u: Annotated[list[float] | None, ListLen("npft")] = None
    """Term proportional to wind speed in the background unloading rate for snow on canopy."""
    i_snow_cond_parm: int | None = Field(default=None, ge=0, le=1)
    """Scheme used to calculate the conductivity of snow."""
    l_et_metamorph: bool = False
    """Include the effect of thermal metamorphism on the snow density."""
    l_snow_infilt: bool = False
    """Pass rainfall and melting from the canopy to the snowpack as infiltration."""
    l_snow_nocan_hc: bool = False
    """Do not include the canopy heat capacity in surface energy balance at snow pack top."""
    a_snow_et: float | None = None
    """Constant in parametrization of thermal metamorphism."""
    b_snow_et: float | None = None
    """Constant in parametrization of thermal metamorphism."""
    c_snow_et: float | None = None
    """Constant in parametrization of thermal metamorphism."""
    rho_snow_et_crit: float | None = None
    """Critical density in parametrization of thermal metamorphism."""
    i_grain_growth_opt: int = Field(default=0, ge=0, le=1)
    """Scheme used to calculate the rate of growth of snow grains."""
    i_relayer_opt: int = Field(default=0, ge=0, le=1)
    """Scheme used to relayer the snowpack."""
    i_basal_melting_opt: int = Field(default=0, ge=0, le=1)
    """Option to treat basal melting of the snow pack."""

    @model_validator(mode="after")
    def _check_dzsnow_length(self) -> "JulesSnow":
        if self.nsmax > 0 and self.dzsnow is None:
            raise ValueError("dzsnow is required when nsmax > 0")
        if self.dzsnow is not None and len(self.dzsnow) != self.nsmax:
            raise ValueError(
                f"dzsnow has {len(self.dzsnow)} element(s), expected nsmax={self.nsmax}"
            )
        return self


class JulesSnowNamelist(NamelistModel):
    """Top-level schema for `jules_snow.nml`."""

    jules_snow: JulesSnow = JulesSnow()
