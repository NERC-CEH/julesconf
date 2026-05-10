"""Validation schema for ``jules_vegetation.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_vegetation.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["JulesVegetationNamelist"]


class JulesVegetation(BaseModel):
    """``JULES_VEGETATION`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_trait_phys: bool = False
    """Switch for using trait-based physiology."""
    l_phenol: bool = False
    """Switch for vegetation phenology model."""
    l_triffid: bool = False
    """Switch for dynamic vegetation model (TRIFFID) except for competition."""
    l_veg_compete: bool = True
    """Switch for competing vegetation."""
    l_trif_eq: bool = False
    """Switch for equilibrium vegetation model."""
    l_trif_fire: bool = False
    """Switch for interactive fire used with dynamic vegetation."""
    l_inferno: bool = False
    """Switch for interactive fires (INFERNO)."""
    l_nitrogen: bool = False
    """Enable nitrogen limitation of carbon uptake."""
    l_vegcan_soilfx: bool = False
    """Switch for enhancement to canopy model conduction in soil."""
    l_croprotate: bool = False
    """Switch that enables sequential cropping."""
    l_recon: bool = True
    """Switch for reconfiguring vegetation fractions."""

    can_model: int = Field(default=1, ge=1, le=4)
    """Choice of canopy model for vegetation."""
    can_rad_mod: int = Field(default=1, ge=1, le=6)
    """Options for treatment of canopy radiation."""
    ilayers: int = Field(default=10, ge=1)
    """Number of layers for canopy radiation model."""
    photo_model: int = Field(default=1, ge=1, le=2)
    """Choice for model of leaf photosynthesis."""
    stomata_model: int = Field(default=1, ge=1, le=2)
    """Choice for model of stomatal conductance."""

    triffid_period: int | None = None
    """Period for calls to TRIFFID model in days."""
    fsmc_shape: int = Field(default=0, ge=0, le=1)
    """Shape of soil moisture stress function on vegetation."""
    ignition_method: int = Field(default=1, ge=1, le=3)
    """Switch to determine the type of ignition used."""


class JulesVegetationNamelist(BaseModel):
    """Top-level schema for ``jules_vegetation.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_vegetation: JulesVegetation
