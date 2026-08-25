"""Validation schema for `jules_hydrology.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_hydrology.nml.rst`
"""

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive

__all__ = ["JulesHydrology", "JulesHydrologyNamelist"]


class JulesHydrology(NamelistModel):
    """`JULES_HYDROLOGY` namelist members."""

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

    @model_validator(mode="after")
    def _check_runoff_schemes(self) -> "JulesHydrology":
        """TOPMODEL and PDM are alternatives, and `l_spdmvar` belongs to PDM."""
        fail_if(self.l_top and self.l_pdm, "Can't have TOPMODEL and PDM together")
        fail_if(
            self.l_spdmvar and not self.l_pdm,
            "clarify that l_spdmvar=T can only be used with l_pdm=T",
        )
        return self

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesHydrology":
        """Warn about runoff parameters the selected schemes make inactive."""
        if not self.l_hydrology:
            warn_inactive(
                self,
                ("l_var_rainfrac", "l_top", "l_pdm", "l_limit_gsoil"),
                because="l_hydrology is false",
            )
            return self
        if not self.l_top:
            warn_inactive(
                self,
                ("zw_max", "ti_max", "ti_wetl", "nfita", "l_wetland_unfrozen"),
                because="l_top is false",
            )
        if not self.l_pdm:
            warn_inactive(
                self, ("b_pdm", "dz_pdm", "l_spdmvar"), because="l_pdm is false"
            )
        return self


class JulesHydrologyNamelist(NamelistModel):
    """Top-level schema for `jules_hydrology.nml`."""

    jules_hydrology: JulesHydrology
