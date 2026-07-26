"""Validation schema for `crop_params.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/crop_params.nml.rst`
"""

from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import Fraction, ListLen, NonNegFloat

__all__ = ["CropParamsNamelist", "JulesCropparm"]


class JulesCropparm(NamelistModel):
    """`JULES_CROPPARM` namelist members.

    Contains ncpft-length lists of crop PFT parameters.
    Only required when `JULES_SURFACE_TYPES::ncpft` > 0.
    """

    t_bse_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Base temperature (K)."""
    t_opt_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Optimum temperature (K)."""
    t_max_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Maximum temperature (K)."""
    tt_emr_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    """Thermal time between sowing and emergence (deg Cd)."""
    crit_pp_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    """Critical photoperiod (hours)."""
    pp_sens_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Sensitivity of development rate to photoperiod (hours⁻¹)."""
    rt_dir_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient determining relative growth of roots vertically and horizontally."""
    alpha1_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    alpha2_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    alpha3_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    beta1_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    beta2_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    beta3_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining partitioning."""
    gamma_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    """Coefficient for determining specific leaf area (m² kg⁻¹)."""
    delta_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Coefficient for determining specific leaf area (m² kg⁻¹).

    The exponent of the specific-leaf-area relation, and legitimately
    negative: the JULES defaults are all below zero (-0.0507, -0.1451, …).
    Unbounded, matching the vn7.9 rose metadata.
    """
    remob_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Remobilisation factor: fraction of stem growth partitioned to RESERVEC."""
    cfrac_s_io: Annotated[
        list[Fraction] | None, ListLen("ncpft", tolerates=("npft",))
    ] = None
    """Carbon fraction of dry matter for stems.

    The one `JULES_CROPPARM` member the reference documents as `real(npft)`
    rather than `real(ncpft)`. Everything else points the other way: the rose
    metadata says `ncpft`, every neighbouring member of this namelist is
    `ncpft`, and every real configuration supplies `ncpft` values. julesconf
    therefore takes `ncpft` as canonical, so the parameter groups with the
    other crop parameters under `[[crop_pft]]`, while still tolerating an
    `npft`-length array on input for anything written to the reference's
    spelling. Raised upstream — see `notes/toml_config.md`.
    """
    cfrac_r_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Carbon fraction of dry matter for roots."""
    cfrac_l_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Carbon fraction of dry matter for leaves."""
    allo1_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient relating STEMC to CANHT."""
    allo2_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient relating STEMC to CANHT."""
    mu_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient for calculation of senescence.

    `MIN(mu_io * (dvi - sen_dvi_io) ** nu_io, 1.0)` is the fraction of leaf
    carbon moved to the harvest pool per day once senescence has started.
    """
    nu_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient for calculation of senescence. See `mu_io`."""
    yield_frac_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Fraction of the harvest carbon pool converted to yield carbon.

    Yield is the economically valuable component of the harvest pool, e.g.
    the kernel.
    """
    initial_carbon_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    """Carbon in crop at emergence (kgC m⁻²)."""
    initial_c_dvi_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """DVI at which the crop carbon is set to `initial_carbon_io`.

    Should be at emergence (0.0) or shortly after.
    """
    sen_dvi_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """DVI at which leaf senescence begins."""
    t_mort_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Soil temperature (second level) at which to kill the crop if DVI > 1 (K)."""


class CropParamsNamelist(NamelistModel):
    """Top-level schema for `crop_params.nml`."""

    jules_cropparm: JulesCropparm = JulesCropparm()
