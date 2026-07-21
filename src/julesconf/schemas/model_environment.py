"""Validation schema for `model_environment.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/model_environment.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import name_or_value

__all__ = [
    "JulesModelEnvironment",
    "JulesParent",
    "LsmId",
    "ModelEnvironmentNamelist",
]


class JulesParent(IntEnum):
    """Environment in which JULES is being run (`l_jules_parent`)."""

    standalone = 0
    um = 1
    cable = 2


class LsmId(IntEnum):
    """Land surface model flavour (`lsm_id`)."""

    jules = 1
    cable = 2


class JulesModelEnvironment(NamelistModel):
    """`JULES_MODEL_ENVIRONMENT` namelist members."""

    l_jules_parent: Annotated[JulesParent, name_or_value(JulesParent)] = (
        JulesParent.standalone
    )
    """Environment in which JULES is run: `standalone` (0), `um` (1), `cable` (2)."""
    lsm_id: Annotated[LsmId, name_or_value(LsmId)] = LsmId.jules
    """Land surface model flavour: `jules` (1), `cable` (2)."""


class ModelEnvironmentNamelist(NamelistModel):
    """Top-level schema for `model_environment.nml`."""

    jules_model_environment: JulesModelEnvironment
