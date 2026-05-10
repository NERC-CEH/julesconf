"""Validation schema for ``jules_snow.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_snow.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["JulesSnowNamelist"]


class JulesSnow(BaseModel):
    """``JULES_SNOW`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    nsmax: int = Field(default=0, ge=0)
    l_snowdep_surf: bool = False
    frac_snow_subl_melt: int = Field(default=0, ge=0, le=1)
    graupel_options: int = Field(default=0, ge=0, le=2)

    # Length nsmax (only used if nsmax > 0)
    dzsnow: list[float] | None = None

    # Length npft (cross-namelist — validated in JulesNamelists)
    cansnowpft: list[bool] | None = None

    # Radiation parameters
    r0: float = 50.0
    rmax: float = 2000.0
    snow_ggr: list[float] | None = None  # length 3
    amax: list[float] | None = None  # length 2
    aicemax: list[float] | None = None  # length 2
    maskd: float = 50.0
    dtland: float = 2.0
    kland_numerator: float = 0.3
    can_clump: list[float] | None = None  # length npft
    n_lai_exposed: list[float] | None = None  # length npft
    lai_alb_lim_sn: list[float] | None = None  # length npft

    # Other snow parameters
    rho_snow_const: float = 250.0
    rho_snow_fresh: float = 100.0
    rho_firn_albedo: float = 550.0
    snow_hcon: float = 0.265
    snow_hcap: float = 0.63e6
    snowliqcap: float = 0.05
    snowinterceptfact: float = 0.7
    snowloadlai: float = 4.4
    snowunloadfact: float = 0.4
    unload_rate_cnst: list[float] | None = None  # length npft
    unload_rate_u: list[float] | None = None  # length npft
    i_snow_cond_parm: int | None = Field(default=None, ge=0, le=1)
    l_et_metamorph: bool = False
    l_snow_infilt: bool = False
    l_snow_nocan_hc: bool = False
    a_snow_et: float | None = None
    b_snow_et: float | None = None
    c_snow_et: float | None = None
    rho_snow_et_crit: float | None = None
    i_grain_growth_opt: int = Field(default=0, ge=0, le=1)
    i_relayer_opt: int = Field(default=0, ge=0, le=1)
    i_basal_melting_opt: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def _check_dzsnow_length(self) -> "JulesSnow":
        if self.nsmax > 0 and self.dzsnow is None:
            raise ValueError("dzsnow is required when nsmax > 0")
        if self.dzsnow is not None and len(self.dzsnow) != self.nsmax:
            raise ValueError(
                f"dzsnow has {len(self.dzsnow)} element(s), expected nsmax={self.nsmax}"
            )
        return self


class JulesSnowNamelist(BaseModel):
    """Top-level schema for ``jules_snow.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_snow: JulesSnow = JulesSnow()
