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
    l_phenol: bool = False
    l_triffid: bool = False
    l_veg_compete: bool = True
    l_trif_eq: bool = False
    l_trif_fire: bool = False
    l_inferno: bool = False
    l_nitrogen: bool = False
    l_vegcan_soilfx: bool = False
    l_croprotate: bool = False
    l_recon: bool = True

    can_model: int = Field(default=1, ge=1, le=4)
    can_rad_mod: int = Field(default=1, ge=1, le=6)
    ilayers: int = Field(default=10, ge=1)
    photo_model: int = Field(default=1, ge=1, le=2)
    stomata_model: int = Field(default=1, ge=1, le=2)

    triffid_period: int | None = None
    fsmc_shape: int = Field(default=0, ge=0, le=1)
    ignition_method: int = Field(default=1, ge=1, le=3)


class JulesVegetationNamelist(BaseModel):
    """Top-level schema for ``jules_vegetation.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_vegetation: JulesVegetation
