"""Validation schema for `jules_deposition.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_deposition.nml.rst`
"""

from enum import IntEnum
from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import check_group_count, warn_inactive
from julesconf.schemas.constraints import ListLen, NonNegFloat, name_or_value

__all__ = [
    "DepH2SoilScheme",
    "DryDepModel",
    "JulesDeposition",
    "JulesDepositionNamelist",
    "JulesDepositionSpecies",
    "JulesDepositionSpeciesSpecific",
]


class DryDepModel(IntEnum):
    """Dry deposition model (`dry_dep_model`)."""

    restricted_ukca = 1
    flexible_ukca = 2


class DepH2SoilScheme(IntEnum):
    """Scheme for soil uptake of atmospheric H2 (`dep_h2_soil_scheme`)."""

    conrad_seiler = 1
    paulot = 2


class JulesDeposition(NamelistModel):
    """`JULES_DEPOSITION` namelist members."""

    l_deposition: bool = False
    """Switch to activate deposition code in JULES."""
    ndry_dep_species: int | None = Field(default=None, ge=1, le=200)
    """Number of species for which dry deposition is calculated; the number of `JULES_DEPOSITION_SPECIES` groups JULES reads."""
    dry_dep_model: Annotated[DryDepModel, name_or_value(DryDepModel)] = (
        DryDepModel.restricted_ukca
    )
    """Dry deposition model: `restricted_ukca` (1), `flexible_ukca` (2, the same parameterisation with the surface tile configuration restriction removed)."""
    dep_h2_soil_scheme: Annotated[DepH2SoilScheme, name_or_value(DepH2SoilScheme)] = (
        DepH2SoilScheme.conrad_seiler
    )
    """Soil uptake of atmospheric H2: `conrad_seiler` (1), `paulot` (2). The Paulot scheme is not available in UM-coupled JULES."""
    dzl_const: NonNegFloat | None = None
    """Constant separation of the boundary layer levels (m).

    Every layer thickness is set to this; prescribed data may override it. This
    is the representative depth for tracer concentration and the depth over
    which the deposition flux is removed.
    """
    tundra_s_limit: float | None = Field(default=None, ge=-1.0, le=1.0)
    """Sine of the latitude of the southern limit of tundra.

    Deposition of 'CO', 'NO2', 'O3', 'PAN', 'PPAN', 'MPAN' and 'ONITU' is
    calculated differently north of this limit. The user guide calls this a
    latitude in radians, which contradicts both its own metadata range and the
    shipped configurations.
    """
    l_deposition_flux: bool = False
    """Calculate deposition fluxes rather than deposition velocities.

    Fluxes require the atmospheric tracer concentrations to be supplied as
    prescribed data.
    """
    l_deposition_gc_corr: bool = False
    """Use a stomatal conductance calculated without bare soil evaporation."""
    l_deposition_from_ukca: bool = False
    """Call the JULES deposition routines from `ukca_chemistry_ctl`.

    For UM-coupled JULES only; it must be FALSE in standalone.
    """
    l_ukca_ddep_lev1: bool = False
    """Apply dry deposition losses only from the lowest boundary layer level.

    When FALSE they are applied from every level in the boundary layer.
    """
    l_ukca_ddepo3_ocean: bool = False
    """Use the Luhar et al. (2018) mechanistic calculation for ozone deposition to the ocean.

    When FALSE the water surface resistance from `rsurf_std_io` is used.
    Available only to UM-coupled JULES.
    """
    l_ukca_dry_dep_so2wet: bool = False
    """Account for surface wetness in the dry deposition of SO2.

    Uses the parameterisation of Erisman, Pul and Wyers (1994). Available only
    to UM-coupled JULES.
    """
    l_ukca_emsdrvn_ch4: bool = False
    """The UKCA chemistry scheme uses CH4 emissions rather than prescribed CH4 surface mole fractions."""

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesDeposition":
        """Everything else in the block is read only when deposition is on."""
        if not self.l_deposition:
            warn_inactive(
                self,
                (
                    "ndry_dep_species",
                    "dry_dep_model",
                    "dep_h2_soil_scheme",
                    "dzl_const",
                    "tundra_s_limit",
                    "l_deposition_flux",
                    "l_deposition_gc_corr",
                    "l_ukca_ddep_lev1",
                    "l_ukca_ddepo3_ocean",
                    "l_ukca_dry_dep_so2wet",
                    "l_ukca_emsdrvn_ch4",
                ),
                because="l_deposition is false",
            )
        return self


class JulesDepositionSpecies(NamelistModel):
    """`JULES_DEPOSITION_SPECIES` namelist members.

    JULES reads this group `JULES_DEPOSITION::ndry_dep_species` times, once per
    atmospheric tracer species, so
    `JulesDepositionNamelist.jules_deposition_species` holds a *list* of these
    — one entry per occurrence, in file order.
    """

    dep_species_name_io: str | None = None
    """Name of an atmospheric tracer species to be included in deposition modelling."""
    dep_species_rmm_io: float | None = None
    """Relative molecular mass of the species (g mol⁻¹); used in UKCA and for quasi-laminar resistance calculations."""
    diffusion_coeff_io: float | None = None
    """Molecular diffusion coefficient of the species in air (m² s⁻¹); set to -1.0 if unavailable (calculated from water diffusion coefficient)."""
    rsurf_std_io: Annotated[list[float] | None, ListLen("ntype")] = None
    """Standard surface resistance for each surface type (s m⁻¹); one value per surface type."""
    diffusion_corr_io: float | None = None
    """Diffusion correction factor for stomatal resistance accounting for diffusivity differences (dimensionless)."""
    r_tundra_io: float | None = None
    """Surface resistance used in tundra regions (s m⁻¹)."""
    dd_ice_coeff_io: (
        Annotated[list[float], Field(min_length=3, max_length=3)] | None
    ) = None
    """Three coefficients of the quadratic function relating dry deposition over ice to temperature."""

    _FLEXIBLE_ONLY: ClassVar[tuple[str, ...]] = (
        "dep_species_rmm_io",
        "diffusion_coeff_io",
        "rsurf_std_io",
        "diffusion_corr_io",
        "r_tundra_io",
        "dd_ice_coeff_io",
    )
    """Members read only when `JULES_DEPOSITION::dry_dep_model` is `flexible_ukca`.

    Every member of this block except `dep_species_name_io`, which the rose
    metadata triggers on both values of `dry_dep_model`: the species still has
    to be named whichever scheme is in use.
    """


class JulesDepositionSpeciesSpecific(NamelistModel):
    """`JULES_DEPOSITION_SPECIES_SPECIFIC` namelist members.

    Deposition parameters that apply to exactly one deposited species. Unlike
    `JULES_DEPOSITION_SPECIES`, which JULES reads once per species, this block
    is read **once** — the rose file definition is
    `namelist:jules_deposition (namelist:jules_deposition_species(:))
    (namelist:jules_deposition_species_specific)`, with no repeat marker on the
    last group. It exists to keep species-specific parameters off every species
    block, where all but one occurrence would be redundant.

    Every member is read only when `JULES_DEPOSITION::dry_dep_model` is
    `flexible_ukca`; the restricted scheme hard-wires them in the JULES source.
    """

    # CH4
    ch4_scaling_io: NonNegFloat | None = None
    """Scaling applied to methane soil uptake (dimensionless)."""
    ch4_mml_io: NonNegFloat | None = None
    """Factor converting the methane soil uptake flux (µg m⁻² h⁻¹) to a dry deposition velocity (m s⁻¹)."""
    ch4dd_tundra_io: (
        Annotated[list[float], Field(min_length=4, max_length=4)] | None
    ) = None
    """Four coefficients of the cubic polynomial relating methane loss for tundra to temperature, giving a flux in µg(CH4) m⁻² s⁻¹."""
    ch4_up_flux_io: Annotated[list[NonNegFloat] | None, ListLen("ntype")] = None
    """Methane uptake flux for each surface type (µg(CH4) m⁻² s⁻¹); one value per surface type."""

    # H2
    h2dd_c_io: Annotated[list[float] | None, ListLen("ntype")] = None
    """Constant term of the quadratic relating hydrogen deposition to soil moisture (s m⁻¹); one value per surface type."""
    h2dd_m_io: Annotated[list[float] | None, ListLen("ntype")] = None
    """First order coefficient of the quadratic relating hydrogen deposition to soil moisture (s m⁻¹); one value per surface type."""
    h2dd_q_io: Annotated[list[float] | None, ListLen("ntype")] = None
    """Second order coefficient of the quadratic relating hydrogen deposition to soil moisture (s m⁻¹); one value per surface type."""

    # O3
    cuticle_o3_io: NonNegFloat | None = None
    """Constant used in the calculation of cuticular resistance for ozone (s m⁻¹)."""
    r_wet_soil_o3_io: NonNegFloat | None = None
    """Wet soil surface resistance for ozone (s m⁻¹)."""


class JulesDepositionNamelist(NamelistModel):
    """Top-level schema for `jules_deposition.nml`."""

    jules_deposition: JulesDeposition = JulesDeposition()
    jules_deposition_species_specific: JulesDepositionSpeciesSpecific = (
        JulesDepositionSpeciesSpecific()
    )
    """Parameters specific to a single deposited species. Read once, not once per species."""
    jules_deposition_species: list[JulesDepositionSpecies] = Field(default_factory=list)
    """One entry per `JULES_DEPOSITION_SPECIES` group, in file order.

    Defaults to empty: with deposition off there are no species, and
    `ndry_dep_species` has no JULES default to fall back on.
    """

    @model_validator(mode="after")
    def _check_species_count(self) -> "JulesDepositionNamelist":
        """Check the number of species groups against `ndry_dep_species`."""
        check_group_count(
            "jules_deposition_species",
            self.jules_deposition_species,
            self.jules_deposition.ndry_dep_species,
            count_member="JULES_DEPOSITION::ndry_dep_species",
        )
        return self

    @model_validator(mode="after")
    def _warn_inactive_species_specific(self) -> "JulesDepositionNamelist":
        """The species-specific block is read only by the flexible scheme.

        The metadata triggers every one of its members on
        `dry_dep_model == 2`: the restricted UKCA scheme hard-wires these
        parameters in the JULES source and never reads the block.
        """
        deposition = self.jules_deposition
        if not deposition.l_deposition:
            because = "l_deposition is false"
        elif deposition.dry_dep_model is not DryDepModel.flexible_ukca:
            because = "dry_dep_model is not flexible_ukca"
        else:
            return self
        warn_inactive(
            self.jules_deposition_species_specific,
            tuple(JulesDepositionSpeciesSpecific.model_fields),
            because=because,
        )
        return self

    @model_validator(mode="after")
    def _warn_inactive_species_members(self) -> "JulesDepositionNamelist":
        """Warn about per-species members the deposition scheme does not read.

        With deposition off the whole group is inert; with the restricted UKCA
        scheme only the species name is read, every other parameter being
        hard-wired in the JULES source. Each occurrence is checked separately,
        so a config with one over-specified species is reported once per
        species, not once for the group.
        """
        deposition = self.jules_deposition
        if not deposition.l_deposition:
            members = tuple(JulesDepositionSpecies.model_fields)
            because = "l_deposition is false"
        elif deposition.dry_dep_model is not DryDepModel.flexible_ukca:
            members = JulesDepositionSpecies._FLEXIBLE_ONLY
            because = "dry_dep_model is not flexible_ukca"
        else:
            return self
        for species in self.jules_deposition_species:
            warn_inactive(species, members, because=because)
        return self
