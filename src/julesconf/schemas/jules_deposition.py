"""Validation schema for `jules_deposition.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_deposition.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import check_group_count
from julesconf.schemas.constraints import ListLen

__all__ = [
    "JulesDeposition",
    "JulesDepositionNamelist",
    "JulesDepositionSpecies",
]


class JulesDeposition(NamelistModel):
    """`JULES_DEPOSITION` namelist members."""

    l_deposition: bool = False
    """Switch to activate deposition code in JULES."""
    ndry_dep_species: int | None = Field(default=None, ge=1, le=200)
    """Number of species for which dry deposition is calculated; the number of `JULES_DEPOSITION_SPECIES` groups JULES reads."""


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
