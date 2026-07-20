"""Validation schema for ``jules_soil.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_soil.nml.rst``
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import name_or_value

__all__ = ["JulesSoilNamelist", "SoilhcMethod"]


class SoilhcMethod(IntEnum):
    """Soil thermal conductivity model (``soilhc_method``)."""

    johansen = 1
    peters_lidard = 2
    chadburn = 3


class JulesSoil(NamelistModel):
    """``JULES_SOIL`` namelist members."""

    sm_levels: int = Field(default=4, ge=1)
    """Number of soil layers."""
    l_vg_soil: bool = False
    """Switch for van Genuchten soil hydraulic model."""
    l_dpsids_dsdz: bool = False
    """Switch to calculate vertical gradient of soil suction with linearity assumption."""
    l_soil_sat_down: bool = False
    """Switch for dealing with supersaturated soil layers."""
    l_holdwater: bool = False
    """Switch fixing soil hydrology problem where supersaturated moisture is pushed out."""
    l_bedrock: bool = False
    """Switch for using a thermal bedrock column beneath the soil column."""
    l_tile_soil: bool = False
    """Switch to set number of soil tiles equal to number of surface tiles."""
    l_broadcast_ancils: bool = False
    """Switch to allow non-soil tiled ancillary files broadcast to all soil tiles."""
    soilhc_method: Annotated[SoilhcMethod, name_or_value(SoilhcMethod)] = (
        SoilhcMethod.johansen
    )
    """Soil thermal conductivity model: ``johansen`` (1), ``peters_lidard`` (2), ``chadburn`` (3)."""
    cs_min: float = 1.0e-6
    """Minimum allowed soil carbon (kg m⁻²)."""
    zsmc: float = Field(default=1.0, gt=0)
    """Depth to which soil moisture average is calculated if requested (m)."""
    zst: float = Field(default=1.0, gt=0)
    """The depth for averaging soil temperature in wetland methane emissions calculation (m)."""
    confrac: float = Field(default=0.3, ge=0, le=1)
    """The fraction of the gridbox assumed to be covered by convective precipitation."""
    dzsoil_io: list[float] | None = None
    """The soil layer depths (m), starting with the uppermost layer."""
    dzsoil_elev: float | None = None
    """Depth of tiled solid-ice bedrock-type layer under individual ice tiles."""

    # Bedrock parameters (only used if l_bedrock = True)
    ns_deep: int = Field(default=100, ge=1)
    """The number of levels in the thermal-only bedrock."""
    hcapdeep: float = 2100000.0
    """The heat capacity of the bedrock (J K⁻¹ m⁻³)."""
    hcondeep: float = 8.6
    """The heat conductivity of the bedrock (W m⁻² K⁻¹)."""
    dzdeep: float = 0.5
    """The thickness of the bedrock layers (m)."""

    @model_validator(mode="after")
    def _check_dzsoil_length(self) -> "JulesSoil":
        if self.dzsoil_io is not None and len(self.dzsoil_io) != self.sm_levels:
            raise ValueError(
                f"dzsoil_io has {len(self.dzsoil_io)} element(s),"
                f" expected sm_levels={self.sm_levels}"
            )
        return self


class JulesSoilNamelist(NamelistModel):
    """Top-level schema for ``jules_soil.nml``."""

    jules_soil: JulesSoil
