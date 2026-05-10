"""Validation schema for ``jules_deposition.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_deposition.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["JulesDepositionNamelist"]


class JulesDeposition(BaseModel):
    """``JULES_DEPOSITION`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_deposition: bool = False
    """Switch to activate deposition code in JULES."""


class JulesDepositionSpecies(BaseModel):
    """``JULES_DEPOSITION_SPECIES`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    dep_species_name_io: str | None = None
    """Name of an atmospheric tracer species to be included in deposition modelling."""
    dep_species_rmm_io: float | None = None
    """Relative molecular mass of the species (g mol⁻¹); used in UKCA and for quasi-laminar resistance calculations."""
    diffusion_coeff_io: float | None = None
    """Molecular diffusion coefficient of the species in air (m² s⁻¹); set to -1.0 if unavailable (calculated from water diffusion coefficient)."""
    rsurf_std_io: list[float] | None = None
    """Standard surface resistance for each surface type (s m⁻¹); one value per surface type."""
    diffusion_corr_io: float | None = None
    """Diffusion correction factor for stomatal resistance accounting for diffusivity differences (dimensionless)."""
    r_tundra_io: float | None = None
    """Surface resistance used in tundra regions (s m⁻¹)."""
    dd_ice_coeff_io: list[float] | None = None
    """Three coefficients of the quadratic function relating dry deposition over ice to temperature."""


class JulesDepositionNamelist(BaseModel):
    """Top-level schema for ``jules_deposition.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_deposition: JulesDeposition = JulesDeposition()
    jules_deposition_species: JulesDepositionSpecies = JulesDepositionSpecies()
