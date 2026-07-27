"""Validation schema for `jules_deposition.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_deposition.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

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


class JulesDepositionNamelist(NamelistModel):
    """Top-level schema for `jules_deposition.nml`."""

    jules_deposition: JulesDeposition = JulesDeposition()
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
