"""Pydantic validation schemas for JULES namelist files.

Each module corresponds to one JULES namelist file and exposes a top-level
model named after the file (e.g. `TimestepsNamelist` for `timesteps.nml`).
Call `Model.model_validate(data)` where `data` is the dict returned by
reading the file with `julesconf.config.NamelistFileHandler`.

The top-level `julesconf.schemas.JulesNamelists` model
validates a complete namelists directory (output of
`julesconf.config.NamelistConfig.read`), including cross-namelist
consistency checks.

`julesconf.schemas.constraints` holds the reusable field constraints the
namelist modules are built from, for use when adding a schema for a namelist
that does not have one yet.

> **Note:** All models emit a `UnknownNamelistKeyWarning` when they encounter
a key they do not recognise. This surfaces typos (which JULES itself
silently ignores) without rejecting configs that contain members the
schema does not yet cover.
"""

from julesconf.schemas._base import (
    NamelistModel,
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
)
from julesconf.schemas._conditional import InactiveNamelistKeyWarning
from julesconf.schemas._grouped import (
    CropPft,
    GroupedConfigError,
    Nvg,
    Pft,
    ToleratedLengthWarning,
)
from julesconf.schemas._namelists import (
    POSTPONED_NAMELISTS,
    REPEATABLE_GROUPS,
    JulesNamelists,
    PostponedNamelistWarning,
)
from julesconf.schemas.constraints import (
    LIST_LEN_DIMS,
    Fraction,
    ListLen,
    NonNegFloat,
    PerElementDefault,
    SentinelOrFraction,
    ZeroOne,
    name_or_value,
)
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

JULES_VERSION = "7.9"
"""JULES user-guide version the schemas are pinned to."""

__all__ = [
    "JULES_VERSION",
    "LIST_LEN_DIMS",
    "POSTPONED_NAMELISTS",
    "REPEATABLE_GROUPS",
    "CanModel",
    "CanRadMod",
    "Ch4Substrate",
    "CropPft",
    "Fraction",
    "GroupedConfigError",
    "IgnitionMethod",
    "InactiveNamelistKeyWarning",
    "IrrCrop",
    "JulesNamelists",
    "JulesParent",
    "ListLen",
    "LsmId",
    "NamelistModel",
    "NonNegFloat",
    "Nvg",
    "PerElementDefault",
    "Pft",
    "PhotoModel",
    "PostponedNamelistWarning",
    "RepeatedNamelistGroupWarning",
    "RiverRoutingAlgorithm",
    "SentinelOrFraction",
    "SoilBgcModel",
    "SoilhcMethod",
    "StomataModel",
    "ToleratedLengthWarning",
    "UnknownNamelistKeyWarning",
    "ZeroOne",
    "name_or_value",
]
