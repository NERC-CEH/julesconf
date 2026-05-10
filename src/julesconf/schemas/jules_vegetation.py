"""Validation schema for ``jules_vegetation.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_vegetation.nml.rst``
"""

from enum import IntEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from julesconf.schemas._utils import name_or_value

__all__ = [
    "CanModel",
    "CanRadMod",
    "IgnitionMethod",
    "JulesVegetationNamelist",
    "PhotoModel",
    "StomataModel",
]


class CanModel(IntEnum):
    """Canopy model choice for vegetation (``can_model``)."""

    no_canopy = 1
    radiative = 2
    radiative_heat_capacity = 3
    radiative_snow = 4


class CanRadMod(IntEnum):
    """Canopy radiation treatment (``can_rad_mod``).

    Options 2 and 3 are not documented in the v7.9 user guide (likely deprecated).
    """

    beers_law = 1
    option_2 = 2
    option_3 = 3
    two_stream = 4
    two_stream_sunfleck = 5
    two_stream_nitrogen = 6


class PhotoModel(IntEnum):
    """Leaf photosynthesis model (``photo_model``)."""

    collatz = 1
    farquhar_collatz = 2


class StomataModel(IntEnum):
    """Stomatal conductance model (``stomata_model``)."""

    jacobs = 1
    medlyn = 2
    sox = 3


class IgnitionMethod(IntEnum):
    """Ignition type for INFERNO fire model (``ignition_method``)."""

    constant = 1
    prescribed_lightning = 2
    prescribed_population = 3


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

    can_model: Annotated[CanModel, name_or_value(CanModel)] = CanModel.no_canopy
    """Choice of canopy model: ``no_canopy`` (1), ``radiative`` (2), ``radiative_heat_capacity`` (3, deprecated), ``radiative_snow`` (4, preferred)."""
    can_rad_mod: Annotated[CanRadMod, name_or_value(CanRadMod)] = CanRadMod.beers_law
    """Canopy radiation treatment: ``beers_law`` (1), ``two_stream`` (4), ``two_stream_sunfleck`` (5), ``two_stream_nitrogen`` (6)."""
    ilayers: int = Field(default=10, ge=1)
    """Number of layers for canopy radiation model."""
    photo_model: Annotated[PhotoModel, name_or_value(PhotoModel)] = PhotoModel.collatz
    """Leaf photosynthesis model: ``collatz`` (1, C3+C4 Collatz), ``farquhar_collatz`` (2, Farquhar C3 + Collatz C4)."""
    stomata_model: Annotated[StomataModel, name_or_value(StomataModel)] = (
        StomataModel.jacobs
    )
    """Stomatal conductance model: ``jacobs`` (1), ``medlyn`` (2), ``sox`` (3)."""

    triffid_period: int | None = None
    """Period for calls to TRIFFID model in days."""
    fsmc_shape: int = Field(default=0, ge=0, le=1)
    """Shape of soil moisture stress function on vegetation."""
    ignition_method: Annotated[IgnitionMethod, name_or_value(IgnitionMethod)] = (
        IgnitionMethod.constant
    )
    """INFERNO ignition type: ``constant`` (1), ``prescribed_lightning`` (2), ``prescribed_population`` (3)."""


class JulesVegetationNamelist(BaseModel):
    """Top-level schema for ``jules_vegetation.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_vegetation: JulesVegetation
