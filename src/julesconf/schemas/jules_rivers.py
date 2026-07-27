"""Validation schema for `jules_rivers.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_rivers.nml.rst`
"""

from enum import IntEnum
from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import warn_inactive
from julesconf.schemas.constraints import name_or_value

__all__ = [
    "JulesOverbank",
    "JulesRivers",
    "JulesRiversNamelist",
    "RiverRoutingAlgorithm",
]


class RiverRoutingAlgorithm(IntEnum):
    """River routing algorithm (`i_river_vn`)."""

    um_trip = 1
    rfm = 2
    standalone_trip = 3


class JulesRivers(NamelistModel):
    """`JULES_RIVERS` namelist members."""

    l_rivers: bool = False
    """Switch for enabling river routing."""
    i_river_vn: (
        Annotated[RiverRoutingAlgorithm, name_or_value(RiverRoutingAlgorithm)] | None
    ) = None
    """River routing algorithm: `um_trip` (1), `rfm` (2), `standalone_trip` (3)."""
    nstep_rivers: int | None = Field(default=None, ge=1)
    """Number of model timesteps per routing timestep."""
    a_thresh: int | None = None
    """Drainage area threshold (number of cells) used to distinguish river and land points."""
    cland: float | None = Field(default=None, gt=0)
    """Land wave speed for surface flow (m s⁻¹); used by RFM. Suggested: 0.20-0.40."""
    criver: float | None = Field(default=None, gt=0)
    """River wave speed for surface flow (m s⁻¹); used by RFM. Suggested: 0.50-0.62."""
    cbland: float | None = Field(default=None, gt=0)
    """Subsurface land wave speed (m s⁻¹); used by RFM."""
    cbriver: float | None = Field(default=None, gt=0)
    """Subsurface river wave speed (m s⁻¹); used by RFM."""
    retl: float | None = Field(default=None, ge=-1, le=1)
    """Land return flow fraction (resolution-dependent); used by RFM. Suggested: 0.005."""
    retr: float | None = Field(default=None, ge=-1, le=1)
    """River return flow fraction (resolution-dependent); used by RFM. Suggested: 0.005."""
    runoff_factor: float | None = Field(default=None, gt=0)
    """Runoff bias correction factor; used by RFM. Recommended: 1.0."""
    rivers_speed: float | None = Field(default=None, gt=0)
    """Effective river velocity (m s⁻¹); used by TRIP. Suggested: 0.4-0.5."""
    rivers_meander: float | None = Field(default=None, gt=0)
    """Ratio of actual to calculated (straight-line) river lengths; used by TRIP. Suggested: 1.4."""
    l_inland: bool = False
    """Re-route inland basin water back into soil moisture."""
    l_riv_overbank: bool = False
    """Switch for enabling river overbank inundation.

    Only used with `l_rivers` = TRUE; when FALSE the optional `JULES_OVERBANK`
    namelist is not required. The user guide documents this member under both
    `JULES_RIVERS` and `JULES_OVERBANK`; the rose metadata and every shipped
    configuration put it on `JULES_RIVERS`. See `UPSTREAM.md` §1.8.
    """
    lake_water_conserve_method: Literal[1, 2] = 1
    """Selects the field used for lake evaporation conservation: 1 = fqw_lk, 2 = surf_roff."""
    trip_globe_shape: Literal[1, 2] = 2
    """Earth shape used in the UM-TRIP scheme: 1 = spherical, 2 = ellipsoidal."""

    _ROUTING_ONLY: ClassVar[dict[str, tuple[RiverRoutingAlgorithm, ...]]] = {
        "cland": (RiverRoutingAlgorithm.rfm,),
        "criver": (RiverRoutingAlgorithm.rfm,),
        "cbland": (RiverRoutingAlgorithm.rfm,),
        "cbriver": (RiverRoutingAlgorithm.rfm,),
        "retl": (RiverRoutingAlgorithm.rfm,),
        "retr": (RiverRoutingAlgorithm.rfm,),
        "a_thresh": (RiverRoutingAlgorithm.rfm,),
        "runoff_factor": (RiverRoutingAlgorithm.rfm,),
        "rivers_speed": (
            RiverRoutingAlgorithm.um_trip,
            RiverRoutingAlgorithm.standalone_trip,
        ),
        "rivers_meander": (
            RiverRoutingAlgorithm.um_trip,
            RiverRoutingAlgorithm.standalone_trip,
        ),
        "lake_water_conserve_method": (RiverRoutingAlgorithm.um_trip,),
        "trip_globe_shape": (RiverRoutingAlgorithm.um_trip,),
    }
    """Which routing algorithms read each scheme-specific parameter.

    Transcribed from the `namelist:jules_rivers=i_river_vn` `trigger` rules in
    the JULES vn7.9 rose metadata.
    """

    @model_validator(mode="after")
    def _warn_inactive_members(self) -> "JulesRivers":
        """Warn about routing parameters the selected scheme does not read."""
        if not self.l_rivers:
            warn_inactive(
                self,
                (
                    "i_river_vn",
                    "nstep_rivers",
                    "l_inland",
                    "l_riv_overbank",
                    *self._ROUTING_ONLY,
                ),
                because="l_rivers is false",
            )
            return self
        if self.i_river_vn is not None:
            warn_inactive(
                self,
                [
                    member
                    for member, algorithms in self._ROUTING_ONLY.items()
                    if self.i_river_vn not in algorithms
                ],
                because=f"i_river_vn is {self.i_river_vn.name}",
            )
        return self


class JulesOverbank(NamelistModel):
    """`JULES_OVERBANK` namelist members."""

    overbank_model: Literal[1, 2, 3] | None = None
    """Choice of overbank inundation model: 1 = simple, 2 = LISFLOOD, 3 = probability."""
    riv_c: float | None = Field(default=None, ge=0)
    """Coefficient in river depth allometry (dimensionless). Suggested: 0.27."""
    riv_f: float | None = Field(default=None, ge=0)
    """Exponent in river depth allometry (dimensionless). Suggested: 0.30."""
    riv_a: float | None = Field(default=None, ge=0)
    """Coefficient in river width allometry (dimensionless). Suggested: 7.20."""
    riv_b: float | None = Field(default=None, ge=0)
    """Exponent in river width allometry (dimensionless). Suggested: 0.50."""
    coef_b: float | None = None
    """Coefficient in bankfull flow allometry. Suggested: 0.08."""
    exp_c: float | None = None
    """Exponent in bankfull flow allometry. Suggested: 0.95."""
    ent_ratio: float | None = None
    """Rosgen entrenchment ratio used to calculate floodplain width from bankfull width."""


class JulesRiversNamelist(NamelistModel):
    """Top-level schema for `jules_rivers.nml`."""

    jules_rivers: JulesRivers = JulesRivers()
    jules_overbank: JulesOverbank = JulesOverbank()

    @model_validator(mode="after")
    def _warn_inactive_overbank(self) -> "JulesRiversNamelist":
        """`JULES_OVERBANK` is only read when the switch on `JULES_RIVERS` is set."""
        if not self.jules_rivers.l_riv_overbank:
            warn_inactive(
                self.jules_overbank,
                ("overbank_model",),
                because="jules_rivers l_riv_overbank is false",
            )
        return self
