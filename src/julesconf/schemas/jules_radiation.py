"""Validation schema for `jules_radiation.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_radiation.nml.rst`
"""

from pydantic import Field

from julesconf.schemas._base import NamelistModel

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


class JulesRadiationNamelist(NamelistModel):
    """Top-level schema for `jules_radiation.nml`."""

    jules_radiation: JulesRadiation
