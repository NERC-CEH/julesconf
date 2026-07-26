"""Validation schema for `triffid_params.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/triffid_params.nml.rst`
"""

from typing import Annotated

from pydantic import Field

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import Fraction, ListLen, NonNegFloat

__all__ = ["JulesTriffid", "TriffidParamsNamelist"]


class JulesTriffid(NamelistModel):
    """`JULES_TRIFFID` namelist members.

    Only used when `JULES_VEGETATION::l_triffid` = TRUE.

    JULES declares these arrays `real(npft)` but reads only the leading
    `nnpft = npft - ncpft` values, since TRIFFID models natural vegetation and
    crop PFTs are handled by the crop model instead. They are therefore typed
    `nnpft` here -- the length julesconf writes -- while still accepting the
    `npft`-length form that existing configs use.
    """

    crop_io: Annotated[
        list[Annotated[int, Field(ge=0, le=3)]] | None,
        ListLen("nnpft", tolerates=("npft",)),
    ] = None
    """Flag indicating whether the PFT is natural, crop, or pasture."""
    g_area_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Disturbance rate (/360days)."""
    g_grow_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Rate of leaf growth (/360days)."""
    g_root_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Turnover rate for root biomass (/360days)."""
    g_wood_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Turnover rate for woody biomass (/360days)."""
    lai_max_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Maximum LAI."""
    lai_min_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Minimum LAI."""
    alloc_fast_io: Annotated[
        list[Fraction] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Fraction of carbon flux from vegetation to wood products added to fast pool."""
    alloc_med_io: Annotated[
        list[Fraction] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Fraction of carbon flux from vegetation to wood products added to moderate pool."""
    alloc_slow_io: Annotated[
        list[Fraction] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Fraction of carbon flux from vegetation to wood products added to slow pool."""


class TriffidParamsNamelist(NamelistModel):
    """Top-level schema for `triffid_params.nml`."""

    jules_triffid: JulesTriffid = JulesTriffid()
