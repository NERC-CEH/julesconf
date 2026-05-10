"""Validation schema for ``jules_hydrology.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_hydrology.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["JulesHydrologyNamelist"]


class JulesHydrology(BaseModel):
    """``JULES_HYDROLOGY`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_hydrology: bool = False
    l_var_rainfrac: bool = False
    l_top: bool = False
    l_pdm: bool = False
    l_limit_gsoil: bool = False

    # TOPMODEL parameters (only used if l_top = True)
    zw_max: float | None = None
    ti_max: float | None = None
    ti_wetl: float | None = None
    nfita: int | None = None
    l_wetland_unfrozen: bool = False

    # PDM parameters (only used if l_pdm = True)
    dz_pdm: float | None = None
    b_pdm: float | None = None
    l_spdmvar: bool = False
    slope_pdm_max: float | None = None
    s_pdm: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def _check_topmodel_params(self) -> "JulesHydrology":
        if self.l_top:
            for name in ("zw_max", "ti_max", "ti_wetl", "nfita"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} is required when l_top=True")
        return self


class JulesHydrologyNamelist(BaseModel):
    """Top-level schema for ``jules_hydrology.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_hydrology: JulesHydrology
