"""Validation schema for `jules_radiation.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_radiation.nml.rst`
"""

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive

__all__ = ["JulesRadiation", "JulesRadiationNamelist"]

_SEA_ALB_METHODS = (1, 2, 3, 4, 5)


class JulesRadiation(NamelistModel):
    """`JULES_RADIATION` namelist members."""

    l_cosz: bool = True
    """Switch for calculation of solar zenith angle."""
    l_spec_albedo: bool = False
    """Switch for the two-stream spectral land-surface albedo model."""
    l_spec_alb_bs: bool = False
    """Switch for albedo model when spectral albedo is being used."""
    l_niso_direct: bool = False
    """Switch for using full non-isotropic expression for direct scattering in plant canopies."""
    l_snow_albedo: bool = False
    """Switch for using prognostic snow properties in model albedo."""
    l_embedded_snow: bool = False
    """Switch to account for pft LAI and pft height in calculation of snow albedo."""
    l_dolr_land_black: bool = False
    """Do not use the surface emissivity when adjusting the OLR at land points.

    Has no effect in JULES standalone. Documented only in the rose metadata.
    """
    l_sea_alb_var_chl: bool = False
    """Use a spatially varying chlorophyll content for the open sea albedos.

    Not available to JULES standalone. Documented only in the rose metadata.
    """
    l_mask_snow_orog: bool = False
    """Switch for orographic masking of snow, which decreases albedo in mountainous regions."""
    l_albedo_obs: bool = False
    """Switch for applying a scaling factor to albedo values to match observations."""
    l_spec_sea_alb: bool = False
    """Switch to use spectrally varying open sea albedos."""
    l_hapke_soil: bool = False
    """Switch to enable Hapke's model of soil albedo to include a zenith-angle dependence."""
    l_partition_albsoil: bool = False
    """Switch to apply a spectral partitioning to the soil albedo."""
    i_sea_alb_method: int | None = Field(default=None, ge=1, le=5)
    """Choice of model for the Ocean Surface Albedo (open water, ice free)."""
    fixed_sea_albedo: float | None = None
    """The global value of sea albedo to use for specific sea albedo methods."""
    wght_alb: list[float] | None = None
    """Weights to form the overall albedo from its components."""
    ratio_albsoil: float | None = None
    """Ratio of the NIR to the VIS albedo of bare soil."""
    swdn_frac_albsoil: float | None = None
    """The fraction of total downward SW radiation assumed to be in the NIR part of the spectrum."""

    @model_validator(mode="after")
    def _check_snow_albedo(self) -> "JulesRadiation":
        """The two snow albedo schemes need the spectral albedo, and exclude each other."""
        fail_if(
            self.l_snow_albedo and not self.l_spec_albedo,
            "Prognostic snow albedo can only be used when l_spec_albedo=T",
        )
        fail_if(
            self.l_embedded_snow and not self.l_spec_albedo,
            "If l_embedded_snow = T then l_spec_albedo must also be T",
        )
        fail_if(
            self.l_embedded_snow and self.l_snow_albedo,
            "Embedded canopy snow albedo model is exclusive of l_snow_albedo.",
        )
        return self

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesRadiation":
        """Warn about members that only the spectral albedo scheme reads."""
        if not self.l_spec_albedo:
            warn_inactive(
                self,
                ("l_spec_alb_bs", "l_niso_direct", "l_embedded_snow"),
                because="l_spec_albedo is false",
            )
        return self


class JulesRadiationNamelist(NamelistModel):
    """Top-level schema for `jules_radiation.nml`."""

    jules_radiation: JulesRadiation
