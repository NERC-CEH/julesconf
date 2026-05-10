"""Validation schema for ``urban.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/urban.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["UrbanNamelist"]


class JulesUrban(BaseModel):
    """``JULES_URBAN`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class UrbanNamelist(BaseModel):
    """Top-level schema for ``urban.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_urban: JulesUrban = JulesUrban()
