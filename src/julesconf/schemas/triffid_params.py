"""Validation schema for `triffid_params.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/triffid_params.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import warn_inactive
from julesconf.schemas.constraints import (
    Fraction,
    ListLen,
    NonNegFloat,
    PerElementDefault,
    ZeroOne,
)

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
    retran_l_io: Annotated[
        list[Fraction] | None,
        ListLen("nnpft", tolerates=("npft",)),
        PerElementDefault(0.5, "nnpft"),
    ] = None
    """Fraction of retranslocated leaf N."""
    retran_r_io: Annotated[
        list[Fraction] | None,
        ListLen("nnpft", tolerates=("npft",)),
        PerElementDefault(0.2, "nnpft"),
    ] = None
    """Fraction of retranslocated root N."""
    dpm_rpm_ratio_io: Annotated[
        list[NonNegFloat] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Ratio of decomposable to resistant plant material in the litter input.

    Present in the rose metadata (which carries no description for it) but not
    documented in the v7.9 user guide.
    """

    # --- Agricultural expansion and biocrop harvesting ---
    ag_expand_io: Annotated[
        list[ZeroOne] | None,
        ListLen("nnpft", tolerates=("npft",)),
        PerElementDefault(0, "nnpft"),
    ] = None
    """How the PFT responds when the agricultural area grows.

    `0` is no automatic expansion, `1` plants out the new crop area with this
    PFT. Only used with `JULES_VEGETATION::l_ag_expand` = TRUE.
    """
    harvest_type_io: Annotated[
        list[Annotated[int, Field(ge=0, le=2)]] | None,
        ListLen("nnpft", tolerates=("npft",)),
        PerElementDefault(0, "nnpft"),
    ] = None
    """Kind of harvesting for this PFT.

    `0` is no harvest, `1` is continuous harvest from litter, `2` is periodic
    harvesting at `harvest_freq_io`. Must be `0` for natural PFTs (`crop_io` =
    0). Only used with `JULES_VEGETATION::l_trif_biocrop` = TRUE.
    """
    harvest_freq_io: Annotated[
        list[Annotated[int, Field(ge=0)]] | None,
        ListLen("nnpft", tolerates=("npft",)),
    ] = None
    """Harvest frequency in years. Only used where `harvest_type_io` = 2."""
    harvest_ht_io: Annotated[
        list[float] | None, ListLen("nnpft", tolerates=("npft",))
    ] = None
    """Height (m) to which the PFT is reduced at each harvest cycle.

    Only used where `harvest_type_io` = 2; a placeholder is required for every
    other PFT. `lai_min_io` must be small enough that the PFT height at
    `lai_min_io` does not exceed this, or JULES will not start.

    Unbounded: the user guide's `> 0` cannot be applied to the placeholder
    values the other PFTs must carry, and the rose metadata states no range.
    """

    @model_validator(mode="after")
    def _warn_inactive_harvest_members(self) -> "JulesTriffid":
        """Warn about the harvest parameters no PFT harvests periodically.

        `harvest_freq_io` and `harvest_ht_io` describe the periodic harvest
        cycle, so JULES reads them only when some PFT sets
        `harvest_type_io = 2`. Both carry a placeholder for every other PFT,
        which is why the test is `any`, not "this element".
        """
        if not any(kind == 2 for kind in self.harvest_type_io or ()):
            warn_inactive(
                self,
                ("harvest_freq_io", "harvest_ht_io"),
                because="no PFT sets harvest_type_io = 2",
            )
        return self


class TriffidParamsNamelist(NamelistModel):
    """Top-level schema for `triffid_params.nml`."""

    jules_triffid: JulesTriffid = JulesTriffid()
