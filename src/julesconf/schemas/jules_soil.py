"""Validation schema for ``jules_soil.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_soil.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["JulesSoilNamelist"]


class JulesSoil(BaseModel):
    """``JULES_SOIL`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    sm_levels: int = Field(default=4, ge=1)
    l_vg_soil: bool = False
    l_dpsids_dsdz: bool = False
    l_soil_sat_down: bool = False
    l_holdwater: bool = False
    l_bedrock: bool = False
    l_tile_soil: bool = False
    l_broadcast_ancils: bool = False
    soilhc_method: int = Field(default=1, ge=1, le=3)
    cs_min: float = 1.0e-6
    zsmc: float = Field(default=1.0, gt=0)
    zst: float = Field(default=1.0, gt=0)
    confrac: float = Field(default=0.3, ge=0, le=1)
    dzsoil_io: list[float] | None = None
    dzsoil_elev: float | None = None

    # Bedrock parameters (only used if l_bedrock = True)
    ns_deep: int = Field(default=100, ge=1)
    hcapdeep: float = 2100000.0
    hcondeep: float = 8.6
    dzdeep: float = 0.5

    @model_validator(mode="after")
    def _check_dzsoil_length(self) -> "JulesSoil":
        if self.dzsoil_io is not None and len(self.dzsoil_io) != self.sm_levels:
            raise ValueError(
                f"dzsoil_io has {len(self.dzsoil_io)} element(s),"
                f" expected sm_levels={self.sm_levels}"
            )
        return self


class JulesSoilNamelist(BaseModel):
    """Top-level schema for ``jules_soil.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_soil: JulesSoil
