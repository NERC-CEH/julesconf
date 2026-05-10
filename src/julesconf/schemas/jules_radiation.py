"""Validation schema for ``jules_radiation.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_radiation.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["JulesRadiationNamelist"]

_SEA_ALB_METHODS = (1, 2, 3, 4, 5)


class JulesRadiation(BaseModel):
    """``JULES_RADIATION`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_cosz: bool = True
    l_spec_albedo: bool = False
    l_spec_alb_bs: bool = False
    l_niso_direct: bool = False
    l_snow_albedo: bool = False
    l_embedded_snow: bool = False
    l_mask_snow_orog: bool = False
    l_albedo_obs: bool = False
    l_spec_sea_alb: bool = False
    l_hapke_soil: bool = False
    l_partition_albsoil: bool = False
    i_sea_alb_method: int | None = Field(default=None, ge=1, le=5)
    fixed_sea_albedo: float | None = None
    wght_alb: list[float] | None = None
    ratio_albsoil: float | None = None
    swdn_frac_albsoil: float | None = None


class JulesRadiationNamelist(BaseModel):
    """Top-level schema for ``jules_radiation.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_radiation: JulesRadiation
