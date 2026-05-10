"""Validation schema for ``model_environment.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/model_environment.nml.rst``
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = ["ModelEnvironmentNamelist"]


class JulesModelEnvironment(BaseModel):
    """``JULES_MODEL_ENVIRONMENT`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_jules_parent: Literal[0, 1, 2] = 0
    lsm_id: Literal[1, 2] = 1


class ModelEnvironmentNamelist(BaseModel):
    """Top-level schema for ``model_environment.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_model_environment: JulesModelEnvironment
