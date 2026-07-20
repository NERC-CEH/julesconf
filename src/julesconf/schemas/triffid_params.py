"""Validation schema for ``triffid_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/triffid_params.nml.rst``
"""

from typing import Annotated

from pydantic import Field

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import ListLen, SentinelOrFraction, SentinelOrNonNegFloat

__all__ = ["TriffidParamsNamelist"]


class JulesTriffid(NamelistModel):
    """``JULES_TRIFFID`` namelist members.

    Contains npft-length lists of TRIFFID dynamic vegetation parameters.
    Only used when :nml:mem:`JULES_VEGETATION::l_triffid` = TRUE.
    """

    crop_io: Annotated[
        list[Annotated[int, Field(ge=-1, le=2)]] | None, ListLen("npft")
    ] = None
    """Flag indicating whether the PFT is natural, crop, or pasture."""
    g_area_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Disturbance rate (/360days)."""
    g_grow_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Rate of leaf growth (/360days)."""
    g_root_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Turnover rate for root biomass (/360days)."""
    g_wood_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Turnover rate for woody biomass (/360days)."""
    lai_max_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Maximum LAI."""
    lai_min_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("npft")] = None
    """Minimum LAI."""
    alloc_fast_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of carbon flux from vegetation to wood products added to fast pool."""
    alloc_med_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of carbon flux from vegetation to wood products added to moderate pool."""
    alloc_slow_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of carbon flux from vegetation to wood products added to slow pool."""
    dpm_rpm_ratio_io: Annotated[list[SentinelOrNonNegFloat], ListLen("npft")] | None = (
        None
    )
    """Ratio of DPM to RPM in litter input."""
    retrans_n_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of nitrogen retranslocated from leaves."""
    retrans_p_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of phosphorus retranslocated from leaves."""
    ag_sales_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of agricultural produce sold."""
    ag_plant_io: Annotated[list[SentinelOrFraction] | None, ListLen("npft")] = None
    """Fraction of agricultural produce used for planting."""


class TriffidParamsNamelist(NamelistModel):
    """Top-level schema for ``triffid_params.nml``."""

    jules_triffid: JulesTriffid = JulesTriffid()
