"""Validation schema for `jules_vegetation.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_vegetation.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_discouraged, warn_inactive
from julesconf.schemas.constraints import (
    Fraction,
    ListLen,
    NonNegFloat,
    PerElementDefault,
    name_or_value,
)

__all__ = [
    "CanModel",
    "CanRadMod",
    "FsmcShape",
    "IgnitionMethod",
    "JulesVegetation",
    "JulesVegetationNamelist",
    "PhotoAcclimModel",
    "PhotoActModel",
    "PhotoJvModel",
    "PhotoModel",
    "StomataModel",
]


class FsmcShape(IntEnum):
    """Shape of the soil moisture stress function on vegetation (`fsmc_shape`)."""

    linear_vol = 0
    linear_pot = 1


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


class PhotoAcclimModel(IntEnum):
    """Thermal adaptation/acclimation of photosynthetic capacity (`photo_acclim_model`)."""

    no_acclimation = 0
    thermal_adaptation = 1
    thermal_acclimation = 2
    adaptation_and_acclimation = 3


class PhotoActModel(IntEnum):
    """Model for the activation energies of Jmax and Vcmax (`photo_act_model`)."""

    vary_by_pft = 1
    vary_by_acclimation = 2


class PhotoJvModel(IntEnum):
    """Model for the variation of J25:V25 (`photo_jv_model`)."""

    jmax_only = 1
    total_n_constant = 2


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
    l_ag_expand: bool = False
    """Allow assisted expansion of agricultural crop areas.

    New crop areas are planted out with target PFTs; the kind of expansion is
    set by `JULES_TRIFFID::ag_expand_io`. Requires `l_trif_biocrop`.
    """
    l_rsl_scalar: bool = False
    """Switch for the roughness sublayer correction scheme in scalar variables.

    Based on Harman and Finnigan (2008). Only use when some `l_vegdrag_pft` is TRUE.
    """
    l_nrun_mid_trif: bool = False
    """Start an NRUN part way through a TRIFFID calling period. Only applicable to the UM."""
    l_trif_init_accum: bool = False
    """Start an NRUN resetting accumulated carbon fluxes to zero. Only applicable to the UM."""

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
    fsmc_shape: Annotated[FsmcShape, name_or_value(FsmcShape)] = FsmcShape.linear_vol
    """Shape of soil moisture stress function on vegetation: `linear_vol` (0, piece-wise linear in volumetric soil moisture), `linear_pot` (1, piece-wise linear in soil potential)."""
    ignition_method: Annotated[IgnitionMethod, name_or_value(IgnitionMethod)] = (
        IgnitionMethod.constant
    )
    """INFERNO ignition type: `constant` (1), `prescribed_lightning` (2), `prescribed_population` (3)."""

    # --- Thermal adaptation/acclimation of photosynthesis ---
    photo_acclim_model: Annotated[PhotoAcclimModel, name_or_value(PhotoAcclimModel)] = (
        PhotoAcclimModel.no_acclimation
    )
    """Acclimation of photosynthetic capacity: `no_acclimation` (0), `thermal_adaptation` (1, static home temperature), `thermal_acclimation` (2, dynamic growth temperature), `adaptation_and_acclimation` (3)."""
    photo_act_model: Annotated[PhotoActModel, name_or_value(PhotoActModel)] = (
        PhotoActModel.vary_by_pft
    )
    """Activation energies of Jmax and Vcmax: `vary_by_pft` (1, from `JULES_PFTPARM::act_jmax_io`/`act_vcmax_io`), `vary_by_acclimation` (2, from `act_j_coef`/`act_v_coef`)."""
    photo_jv_model: Annotated[PhotoJvModel, name_or_value(PhotoJvModel)] = (
        PhotoJvModel.jmax_only
    )
    """Variation of J25:V25: `jmax_only` (1, scale V25 by the given ratio), `total_n_constant` (2, hold total photosynthetic nitrogen constant)."""
    act_j_coef: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Coefficients for the activation energy of Jmax (J mol⁻¹; the second and third carry an extra K⁻¹).

    Replaces `JULES_PFTPARM::act_jmax_io` when `photo_act_model` = 2.
    """
    act_v_coef: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Coefficients for the activation energy of Vcmax (J mol⁻¹; the second and third carry an extra K⁻¹).

    Replaces `JULES_PFTPARM::act_vcmax_io` when `photo_act_model` = 2.
    """
    dsj_coef: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Coefficients for the entropy factor of Jmax (J mol⁻¹ K⁻¹; the second and third carry an extra K⁻¹).

    Replaces `JULES_PFTPARM::ds_jmax_io` when `photo_acclim_model` > 0.
    """
    dsv_coef: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Coefficients for the entropy factor of Vcmax (J mol⁻¹ K⁻¹; the second and third carry an extra K⁻¹).

    Replaces `JULES_PFTPARM::ds_vcmax_io` when `photo_acclim_model` > 0.
    """
    jv25_coef: Annotated[list[float], Field(min_length=3, max_length=3)] | None = None
    """Coefficients for the ratio J25:V25 (mol electrons per mol CO₂; the second and third carry an extra K⁻¹).

    Replaces `JULES_PFTPARM::jv25_ratio_io` when `photo_acclim_model` > 0.
    """
    n_alloc_jmax: float | None = None
    """Constant relating nitrogen allocation to Jmax (mol CO₂ m⁻² s⁻¹ per kg m⁻²).

    Only used with `photo_jv_model` = 2.
    """
    n_alloc_vcmax: float | None = None
    """Constant relating nitrogen allocation to Vcmax (mol CO₂ m⁻² s⁻¹ per kg m⁻²).

    Only used with `photo_jv_model` = 2.
    """
    n_day_photo_acclim: float | None = None
    """Time constant (days) for the moving average of temperature used as growth temperature.

    Only used with `photo_acclim_model` = 2 or 3.
    """

    # --- Roughness sublayer canopy drag (l_vegdrag_pft / l_rsl_scalar) ---
    c1_usuh: NonNegFloat | None = None
    """Ratio of friction velocity to wind speed at the top of a dense canopy.

    Only use when some `l_vegdrag_pft` is TRUE. See Massman (1997).
    """
    c2_usuh: NonNegFloat | None = None
    """Ratio of friction velocity to wind speed at the substrate under the canopy.

    Only use when some `l_vegdrag_pft` is TRUE. See Massman (1997).
    """
    c3_usuh: NonNegFloat | None = None
    """Exponent coefficient weighting dense and sparse vegetation for u*/U(h) in neutral conditions.

    Only use when some `l_vegdrag_pft` is TRUE. See Massman (1997).
    """
    cd_leaf: Fraction | None = None
    """Leaf-level drag coefficient. Only use when some `l_vegdrag_pft` is TRUE."""
    stanton_leaf: Fraction | None = None
    """Leaf-level Stanton number. Only used with `l_rsl_scalar` = TRUE.

    Note that `JULES_PFTPARM::z0v_io` is the per-PFT roughness length the drag
    scheme uses when `l_spec_veg_z0` is TRUE.
    """

    @model_validator(mode="after")
    def _warn_deprecated_can_model(self) -> "JulesVegetation":
        """`can_model = 3` is deprecated upstream in favour of 4."""
        warn_discouraged(
            self.can_model == CanModel.radiative_heat_capacity,
            "can_model = 3 is deprecated, with 4 preferred",
        )
        return self

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
        fail_if(
            self.l_ag_expand and not self.l_trif_biocrop,
            "l_ag_expand requires l_trif_biocrop = TRUE",
        )
        return self

    @model_validator(mode="after")
    def _check_photosynthesis_models(self) -> "JulesVegetation":
        """Without acclimation, the activation-energy and J:V models must be per-PFT."""
        if self.photo_acclim_model == PhotoAcclimModel.no_acclimation:
            fail_if(
                self.photo_act_model != PhotoActModel.vary_by_pft,
                "photo_act_model must be vary_by_pft (1) when photo_acclim_model is "
                "no_acclimation (0)",
            )
            fail_if(
                self.photo_jv_model != PhotoJvModel.jmax_only,
                "photo_jv_model must be jmax_only (1) when photo_acclim_model is "
                "no_acclimation (0)",
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
        if not self.l_rsl_scalar:
            warn_inactive(self, ("stanton_leaf",), because="l_rsl_scalar is false")
        if self.photo_acclim_model == PhotoAcclimModel.no_acclimation:
            warn_inactive(
                self,
                ("dsj_coef", "dsv_coef", "jv25_coef"),
                because="photo_acclim_model is no_acclimation",
            )
        if self.photo_acclim_model not in (
            PhotoAcclimModel.thermal_acclimation,
            PhotoAcclimModel.adaptation_and_acclimation,
        ):
            warn_inactive(
                self,
                ("n_day_photo_acclim",),
                because="photo_acclim_model is neither thermal_acclimation nor "
                "adaptation_and_acclimation",
            )
        if self.photo_act_model != PhotoActModel.vary_by_acclimation:
            warn_inactive(
                self,
                ("act_j_coef", "act_v_coef"),
                because="photo_act_model is not vary_by_acclimation",
            )
        if self.photo_jv_model != PhotoJvModel.total_n_constant:
            warn_inactive(
                self,
                ("n_alloc_jmax", "n_alloc_vcmax"),
                because="photo_jv_model is not total_n_constant",
            )
        return self


class JulesVegetationNamelist(NamelistModel):
    """Top-level schema for `jules_vegetation.nml`."""

    jules_vegetation: JulesVegetation
