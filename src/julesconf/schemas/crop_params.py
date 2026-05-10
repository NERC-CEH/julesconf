"""Validation schema for ``crop_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/crop_params.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["CropParamsNamelist"]


class JulesCropparm(BaseModel):
    """``JULES_CROPPARM`` namelist members.

    Contains ncpft-length lists of crop PFT parameters.
    Only required when :nml:mem:`JULES_SURFACE_TYPES::ncpft` > 0.
    """

    model_config = ConfigDict(extra="ignore")

    t_bse_io: list[float] | None = None
    """Base temperature (K)."""
    t_opt_io: list[float] | None = None
    """Optimum temperature (K)."""
    t_max_io: list[float] | None = None
    tt_emr_io: list[float] | None = None
    """Thermal time between sowing and emergence (deg Cd)."""
    crit_pp_io: list[float] | None = None
    """Critical photoperiod (hours)."""
    pp_sens_io: list[float] | None = None
    """Sensitivity of development rate to photoperiod (hours⁻¹)."""
    rt_dir_io: list[float] | None = None
    """Coefficient determining relative growth of roots vertically and horizontally."""
    alpha1_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    alpha2_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    alpha3_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    beta1_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    beta2_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    beta3_io: list[float] | None = None
    """Coefficient for determining partitioning."""
    gamma_io: list[float] | None = None
    """Coefficient for determining specific leaf area (m² kg⁻¹)."""
    delta_io: list[float] | None = None
    """Coefficient for determining specific leaf area (m² kg⁻¹)."""
    remob_io: list[float] | None = None
    """Remobilisation factor: fraction of stem growth partitioned to RESERVEC."""
    cfrac_s_io: list[float] | None = None
    """Carbon fraction of dry matter for stems."""
    cfrac_r_io: list[float] | None = None
    """Carbon fraction of dry matter for roots."""
    cfrac_l_io: list[float] | None = None
    """Carbon fraction of dry matter for leaves."""
    allo1_io: list[float] | None = None
    """Allometric coefficient relating STEMC to CANHT."""
    allo2_io: list[float] | None = None
    """Allometric coefficient relating STEMC to CANHT."""
    mu_max_io: list[float] | None = None
    nu_io: list[float] | None = None
    """Allometric coefficient for calculation of senescence."""


class CropParamsNamelist(BaseModel):
    """Top-level schema for ``crop_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_cropparm: JulesCropparm = JulesCropparm()
