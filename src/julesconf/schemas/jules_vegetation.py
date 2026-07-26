"""Validation schema for `jules_vegetation.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_vegetation.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive
from julesconf.schemas.constraints import (
    ListLen,
    PerElementDefault,
    name_or_value,
)

__all__ = [
    "CanModel",
    "CanRadMod",
    "IgnitionMethod",
    "JulesVegetation",
    "JulesVegetationNamelist",
    "PhotoModel",
    "StomataModel",
]


class CanModel(IntEnum):
    """Canopy model choice for vegetation (`can_model`)."""

    no_canopy = 1
    radiative = 2
    radiative_heat_capacity = 3
    radiative_snow = 4


class CanRadMod(IntEnum):
    """Canopy radiation treatment (`can_rad_mod`).

    Options 2 and 3 are not documented in the v7.9 user guide (likely deprecated).
    """

    beers_law = 1
    option_2 = 2
    option_3 = 3
    two_stream = 4
    two_stream_sunfleck = 5
    two_stream_nitrogen = 6


class PhotoModel(IntEnum):
    """Leaf photosynthesis model (`photo_model`)."""

    collatz = 1
    farquhar_collatz = 2


class StomataModel(IntEnum):
    """Stomatal conductance model (`stomata_model`)."""

    jacobs = 1
    medlyn = 2
    sox = 3


class IgnitionMethod(IntEnum):
    """Ignition type for INFERNO fire model (`ignition_method`)."""

    constant = 1
    prescribed_lightning = 2
    prescribed_population = 3


class JulesVegetation(NamelistModel):
    """`JULES_VEGETATION` namelist members."""

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
    l_bvoc_emis: bool = False
    """Switch to enable calculation of BVOC emission diagnostics."""
    l_gleaf_fix: bool = True
    """Switch for fixing a bug in the accumulation of `g_leaf_phen_acc`."""
    l_ht_compete: bool = False
    """Switch for height-based vegetation competition. Only used with TRIFFID."""
    l_landuse: bool = False
    """Switch for using land use change in conjunction with TRIFFID."""
    l_leaf_n_resp_fix: bool = False
    """Switch for the corrected canopy-average leaf nitrogen used in respiration.

    Affects `can_rad_mod` 1, 4 and 5; 6 is already correct. Retained for
    backwards compatibility with existing configurations.
    """
    l_limit_canhc: bool = False
    """Switch for capping the vegetation canopy areal thermal heat capacity."""
    l_o3_damage: bool = False
    """Switch for ozone damage to vegetation. Not available to the UM."""
    l_prescsow: bool = False
    """Switch for prescribed crop sowing dates. Only used when `ncpft` > 0."""
    l_red: bool = False
    """Switch for the Robust Ecosystem Demography (RED). Not available to the UM."""
    l_scale_resp_pm: bool = False
    """Scale whole-plant maintenance respiration by the soil moisture stress factor.

    When false, only leaf respiration is scaled.
    """
    l_spec_veg_z0: bool = False
    """Switch for explicitly specified vegetation roughness lengths.

    When false they are derived from the canopy height.
    """
    l_stem_resp_fix: bool = False
    """Switch for using balanced LAI to derive respiring stem mass."""
    l_sugar: bool = False
    """Switch for using the SUGAR carbohydrate model to calculate respiration."""
    l_trif_biocrop: bool = False
    """Allow periodic harvesting of bioenergy crops. Requires `l_trif_crop`."""
    l_trif_crop: bool = False
    """Switch for using agricultural PFTs, as defined by `JULES_TRIFFID::crop_io`."""
    l_use_pft_psi: bool = False
    """Calculate the soil moisture stress function from `psi_close_io`/`psi_open_io`.

    Not available to the UM.
    """
    l_vegdrag_pft: Annotated[
        list[bool] | None, ListLen("npft"), PerElementDefault(False, "npft")
    ] = None
    """Switch for using the vegetation canopy drag scheme, per PFT."""

    can_model: Annotated[CanModel, name_or_value(CanModel)] = CanModel.no_canopy
    """Choice of canopy model: `no_canopy` (1), `radiative` (2), `radiative_heat_capacity` (3, deprecated), `radiative_snow` (4, preferred)."""
    can_rad_mod: Annotated[CanRadMod, name_or_value(CanRadMod)] = CanRadMod.beers_law
    """Canopy radiation treatment: `beers_law` (1), `two_stream` (4), `two_stream_sunfleck` (5), `two_stream_nitrogen` (6)."""
    ilayers: int = Field(default=10, ge=1)
    """Number of layers for canopy radiation model."""
    photo_model: Annotated[PhotoModel, name_or_value(PhotoModel)] = PhotoModel.collatz
    """Leaf photosynthesis model: `collatz` (1, C3+C4 Collatz), `farquhar_collatz` (2, Farquhar C3 + Collatz C4)."""
    stomata_model: Annotated[StomataModel, name_or_value(StomataModel)] = (
        StomataModel.jacobs
    )
    """Stomatal conductance model: `jacobs` (1), `medlyn` (2), `sox` (3)."""

    triffid_period: int | None = None
    """Period for calls to TRIFFID model in days."""
    phenol_period: int | None = Field(default=None, ge=1)
    """Period for calls to the phenology model in days. Only used with `l_phenol`."""
    frac_min: float = 1.0e-6
    """Minimum fraction a PFT is allowed to cover if TRIFFID is used."""
    frac_seed: float = 0.01
    """Seed fraction for TRIFFID."""
    pow: float = 5.241e-4
    """Power in the sigmoidal function used to get competition coefficients."""
    fsmc_shape: int = Field(default=0, ge=0, le=1)
    """Shape of soil moisture stress function on vegetation."""
    ignition_method: Annotated[IgnitionMethod, name_or_value(IgnitionMethod)] = (
        IgnitionMethod.constant
    )
    """INFERNO ignition type: `constant` (1), `prescribed_lightning` (2), `prescribed_population` (3)."""

    @model_validator(mode="after")
    def _check_triffid_switches(self) -> "JulesVegetation":
        """Check the TRIFFID sub-switches against each other."""
        fail_if(
            self.l_trif_crop and self.l_trif_eq,
            "l_trif_crop cannot be used with the equilibrium model (l_trif_eq)",
        )
        fail_if(
            self.l_trif_fire and self.l_trif_eq,
            "l_trif_fire cannot be used with the equilibrium model (l_trif_eq)",
        )
        fail_if(
            self.l_trif_biocrop and not self.l_trif_crop,
            "l_trif_biocrop requires l_trif_crop = TRUE",
        )
        return self

    @model_validator(mode="after")
    def _check_crop_switches(self) -> "JulesVegetation":
        """Sequential cropping needs prescribed sowing dates."""
        fail_if(
            self.l_croprotate and not self.l_prescsow,
            "l_prescsow must be TRUE if l_croprotate = TRUE",
        )
        return self

    @model_validator(mode="after")
    def _check_stomata_model(self) -> "JulesVegetation":
        """The SOx stomatal conductance model constrains its neighbours."""
        if self.stomata_model == StomataModel.sox:
            fail_if(
                self.l_scale_resp_pm,
                "stomata_model = sox cannot be used with l_scale_resp_pm = TRUE",
            )
            fail_if(
                self.can_rad_mod != CanRadMod.beers_law,
                "stomata_model = sox requires can_rad_mod = beers_law",
            )
        return self

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesVegetation":
        """Warn about members the vegetation switches make inactive."""
        if not self.l_triffid:
            warn_inactive(
                self,
                (
                    "l_trif_eq",
                    "triffid_period",
                    "l_veg_compete",
                    "l_landuse",
                    "l_ht_compete",
                    "l_nitrogen",
                    "l_red",
                    "l_trif_crop",
                    "l_trif_fire",
                    "frac_min",
                    "frac_seed",
                    "pow",
                ),
                because="l_triffid is false",
            )
        elif not self.l_trif_crop:
            warn_inactive(self, ("l_trif_biocrop",), because="l_trif_crop is false")
        if not self.l_phenol:
            warn_inactive(self, ("phenol_period",), because="l_phenol is false")
        return self


class JulesVegetationNamelist(NamelistModel):
    """Top-level schema for `jules_vegetation.nml`."""

    jules_vegetation: JulesVegetation
