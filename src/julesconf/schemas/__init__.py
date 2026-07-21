"""Pydantic validation schemas for JULES namelist files.

Each module corresponds to one JULES namelist file and exposes a top-level
model named after the file (e.g. `TimestepsNamelist` for `timesteps.nml`).
Call `Model.model_validate(data)` where `data` is the dict returned by
reading the file with `julesconf.config.NamelistFileHandler`.

The top-level `julesconf.schemas.namelists.JulesNamelists` model
validates a complete namelists directory (output of
`julesconf.config.NamelistConfig.read`), including cross-namelist
consistency checks.

> **Note:** All models emit a `UnknownNamelistKeyWarning` when they encounter
a key they do not recognise. This surfaces typos (which JULES itself
silently ignores) without rejecting configs that contain members the
schema does not yet cover.
"""

from julesconf.schemas._base import UnknownNamelistKeyWarning
from julesconf.schemas.jules_irrig import IrrCrop
from julesconf.schemas.jules_rivers import RiverRoutingAlgorithm
from julesconf.schemas.jules_soil import SoilhcMethod
from julesconf.schemas.jules_soil_biogeochem import Ch4Substrate, SoilBgcModel
from julesconf.schemas.jules_vegetation import (
    CanModel,
    CanRadMod,
    IgnitionMethod,
    PhotoModel,
    StomataModel,
)
from julesconf.schemas.model_environment import JulesParent, LsmId
from julesconf.schemas.namelists import JulesNamelists

JULES_VERSION = "7.9"
"""JULES user-guide version the schemas are pinned to."""

__all__ = [
    "JULES_VERSION",
    "CanModel",
    "CanRadMod",
    "Ch4Substrate",
    "IgnitionMethod",
    "IrrCrop",
    "JulesNamelists",
    "JulesParent",
    "LsmId",
    "PhotoModel",
    "RiverRoutingAlgorithm",
    "SoilBgcModel",
    "SoilhcMethod",
    "StomataModel",
    "UnknownNamelistKeyWarning",
]
