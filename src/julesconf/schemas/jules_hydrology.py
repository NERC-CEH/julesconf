"""Validation schema for ``jules_hydrology.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_hydrology.nml.rst``
"""

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel

__all__ = ["JulesHydrologyNamelist"]


class JulesHydrology(NamelistModel):
    """``JULES_HYDROLOGY`` namelist members."""

    l_hydrology: bool = False
    """Switch to enable soil hydrology."""
    l_var_rainfrac: bool = False
    """Switch to enable variable large scale and convective rain fractions."""
    l_top: bool = False
    """Switch for a TOPMODEL-type model of runoff production."""
    l_pdm: bool = False
    """Switch for a PDM-type model of runoff production."""
    l_limit_gsoil: bool = False
    """Limit the soil conductance to the value when the top layer soil moisture is at critical point."""

    # TOPMODEL parameters (only used if l_top = True)
    zw_max: float | None = None
    """The maximum allowed depth to the water table (m)."""
    ti_max: float | None = None
    """The maximum possible value of the topographic index."""
    ti_wetl: float | None = None
    """A calibration parameter used in the calculation of the wetland fraction."""
    nfita: int | None = None
    """The number of values tried when fitting wetland and saturation fractions to water table depth."""
    l_wetland_unfrozen: bool = False
    """Treat the calculations of wetland and surface saturation fractions like an unfrozen soil."""

    # PDM parameters (only used if l_pdm = True)
    dz_pdm: float | None = None
    """The depth of soil considered by PDM (m)."""
    b_pdm: float | None = None
    """PDM shape parameter (exponent) of the Pareto distribution controlling spatial variability."""
    l_spdmvar: bool = False
    """Use a linear function of topographic slope to calculate S0/Smax."""
    slope_pdm_max: float | None = None
    """The maximum topographic slope (deg) in the linear function of slope to calculate S0/Smax."""
    s_pdm: float | None = Field(default=None, ge=0, le=1)
    """Minimum soil water storage below which there is no saturation excess runoff from PDM."""

    @model_validator(mode="after")
    def _check_topmodel_params(self) -> "JulesHydrology":
        if self.l_top:
            for name in ("zw_max", "ti_max", "ti_wetl", "nfita"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name} is required when l_top=True")
        return self


class JulesHydrologyNamelist(NamelistModel):
    """Top-level schema for ``jules_hydrology.nml``."""

    jules_hydrology: JulesHydrology
