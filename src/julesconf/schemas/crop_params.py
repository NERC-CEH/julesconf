"""Validation schema for `crop_params.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/crop_params.nml.rst`
"""

from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import Fraction, ListLen, NonNegFloat

__all__ = ["CropParamsNamelist"]


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
    delta_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    """Coefficient for determining specific leaf area (m² kg⁻¹)."""
    remob_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Remobilisation factor: fraction of stem growth partitioned to RESERVEC."""
    cfrac_s_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Carbon fraction of dry matter for stems."""
    cfrac_r_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Carbon fraction of dry matter for roots."""
    cfrac_l_io: Annotated[list[Fraction] | None, ListLen("ncpft")] = None
    """Carbon fraction of dry matter for leaves."""
    allo1_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient relating STEMC to CANHT."""
    allo2_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient relating STEMC to CANHT."""
    mu_max_io: Annotated[list[NonNegFloat] | None, ListLen("ncpft")] = None
    nu_io: Annotated[list[float] | None, ListLen("ncpft")] = None
    """Allometric coefficient for calculation of senescence."""


class CropParamsNamelist(NamelistModel):
    """Top-level schema for `crop_params.nml`."""

    jules_cropparm: JulesCropparm = JulesCropparm()
