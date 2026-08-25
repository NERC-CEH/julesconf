"""Validation schema for `jules_soil.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_soil.nml.rst`
"""

from collections.abc import Mapping
from enum import IntEnum
from typing import Annotated, Any

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive
from julesconf.schemas.constraints import ListLen, name_or_value

__all__ = ["JulesSoil", "JulesSoilNamelist", "SoilhcMethod"]


class SoilhcMethod(IntEnum):
    """Soil thermal conductivity model (`soilhc_method`)."""

    johansen = 1
    peters_lidard = 2
    chadburn = 3


class JulesSoil(NamelistModel):
    """`JULES_SOIL` namelist members."""

    sm_levels: int = Field(default=4, ge=1)
    """Number of soil layers.

    Derived from the length of `dzsoil_io` when that is given and `sm_levels`
    is not, so a configuration that lists the layer depths need not also state
    how many there are. An explicit value always wins and is still checked
    against `dzsoil_io`.
    """
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
    """Soil thermal conductivity model: `johansen` (1), `peters_lidard` (2), `chadburn` (3)."""
    cs_min: float = 1.0e-6
    """Minimum allowed soil carbon (kg m⁻²)."""
    zsmc: float = Field(default=1.0, gt=0)
    """Depth to which soil moisture average is calculated if requested (m)."""
    zst: float = Field(default=1.0, gt=0)
    """The depth for averaging soil temperature in wetland methane emissions calculation (m)."""
    confrac: float = Field(default=0.3, ge=0, le=1)
    """The fraction of the gridbox assumed to be covered by convective precipitation."""
    dzsoil_io: Annotated[list[float] | None, ListLen("sm_levels")] = None
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

    @model_validator(mode="before")
    @classmethod
    def _derive_sm_levels(cls, data: Any) -> Any:
        """Fill in `sm_levels` from the length of `dzsoil_io` when it is omitted.

        A configuration that lists the layer depths has already said how many
        layers there are, so restating the count is redundant. This fills the
        gap and nothing more:

        - An explicit `sm_levels` always wins. It is never overwritten, so
          `_check_dzsoil_length` still catches a real disagreement between the
          two rather than papering over it.
        - The test is whether `sm_levels` appears in the *raw input*, not
          whether it differs from the default, so a configuration that means
          `sm_levels = 4` is indistinguishable from one that omits it only
          when `dzsoil_io` also has four elements — in which case the two
          answers coincide.

        The `to_namelist_dict` round-trip is unaffected for the same reason:
        it writes `sm_levels` explicitly, so the derivation does not fire, and
        the value it writes came from a configuration the length check already
        passed.
        """
        if not isinstance(data, Mapping):
            return data
        if data.get("sm_levels") is not None:
            return data
        dzsoil = data.get("dzsoil_io")
        if dzsoil is None:
            return data
        # Fortran writes a one-element array indistinguishably from a scalar,
        # which `NamelistModel` coerces to a list; either form means one layer.
        length = len(dzsoil) if isinstance(dzsoil, (list, tuple)) else 1
        if length == 0:
            return data
        return {**data, "sm_levels": length}

    @model_validator(mode="after")
    def _check_dzsoil_length(self) -> "JulesSoil":
        if self.dzsoil_io is not None and len(self.dzsoil_io) != self.sm_levels:
            raise ValueError(
                f"dzsoil_io has {len(self.dzsoil_io)} element(s),"
                f" expected sm_levels={self.sm_levels}"
            )
        return self

    @model_validator(mode="after")
    def _check_dzsoil_elev(self) -> "JulesSoil":
        """The elevated-tile bedrock layer must have a positive thickness."""
        fail_if(
            self.dzsoil_elev is not None and self.dzsoil_elev <= 0,
            "Must have positive value",
        )
        return self

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesSoil":
        """Warn about bedrock parameters set while the bedrock is switched off."""
        if not self.l_bedrock:
            warn_inactive(
                self,
                ("ns_deep", "hcapdeep", "hcondeep", "dzdeep"),
                because="l_bedrock is false",
            )
        return self


class JulesSoilNamelist(NamelistModel):
    """Top-level schema for `jules_soil.nml`."""

    jules_soil: JulesSoil
