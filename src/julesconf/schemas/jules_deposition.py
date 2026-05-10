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


class JulesDepositionSpecies(BaseModel):
    """``JULES_DEPOSITION_SPECIES`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class JulesDepositionNamelist(BaseModel):
    """Top-level schema for ``jules_deposition.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_deposition: JulesDeposition = JulesDeposition()
    jules_deposition_species: JulesDepositionSpecies = JulesDepositionSpecies()
