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
    t_opt_io: list[float] | None = None
    t_max_io: list[float] | None = None
    tt_emr_io: list[float] | None = None
    crit_pp_io: list[float] | None = None
    pp_sens_io: list[float] | None = None
    rt_dir_io: list[float] | None = None
    alpha1_io: list[float] | None = None
    alpha2_io: list[float] | None = None
    alpha3_io: list[float] | None = None
    beta1_io: list[float] | None = None
    beta2_io: list[float] | None = None
    beta3_io: list[float] | None = None
    gamma_io: list[float] | None = None
    delta_io: list[float] | None = None
    remob_io: list[float] | None = None
    cfrac_s_io: list[float] | None = None
    cfrac_r_io: list[float] | None = None
    cfrac_l_io: list[float] | None = None
    allo1_io: list[float] | None = None
    allo2_io: list[float] | None = None
    mu_max_io: list[float] | None = None
    nu_io: list[float] | None = None


class CropParamsNamelist(BaseModel):
    """Top-level schema for ``crop_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_cropparm: JulesCropparm = JulesCropparm()
