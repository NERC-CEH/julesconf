"""Validation schema for ``pft_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/pft_params.nml.rst``

All list fields have length ``npft`` (cross-namelist; validated in
:class:`~julesconf.schemas.namelists.JulesNamelists`).
"""

from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import Fraction, ListLen, NonNegFloat, ZeroOne

__all__ = ["PftParamsNamelist"]


class JulesPftparm(NamelistModel):
    """``JULES_PFTPARM`` namelist members."""

    canht_ft_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """The height of each PFT (m), also known as the canopy height."""
    lai_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """The leaf area index (LAI) of each PFT."""
    c3_io: Annotated[list[ZeroOne] | None, ListLen("npft")] = None
    """Flag indicating whether PFT is C3 type."""
    orient_io: Annotated[list[ZeroOne] | None, ListLen("npft")] = None
    """Flag indicating leaf angle distribution."""
    can_struct_a_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Canopy structure factor (dimensionless)."""
    a_wl_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Allometric coefficient relating target woody biomass to leaf area index."""
    a_ws_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Woody biomass as a multiple of live stem biomass."""
    albsnc_max_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Snow-covered albedo for large leaf area index."""
    albsnc_min_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Snow-covered albedo for zero leaf area index."""
    albsnf_max_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Snow-free albedo for large LAI."""
    albsnf_maxu_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Upper bound for snow-free albedo for large LAI when scaled."""
    albsnf_maxl_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Lower bound for snow-free albedo for large LAI when scaled."""
    alnir_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf reflection coefficient for NIR."""
    alpar_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf reflection coefficient for VIS (photosynthetically active radiation)."""
    alpha_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Quantum efficiency of photosynthesis (mol CO2 per mol PAR photons)."""
    b_wl_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Allometric exponent relating target woody biomass to leaf area index."""
    catch0_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Minimum canopy capacity (kg m⁻²)."""
    dcatch_dlai_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Rate of change of canopy capacity with LAI."""
    dgl_dm_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Rate of change of leaf turnover rate with moisture availability."""
    dgl_dt_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Rate of change of leaf turnover rate with temperature."""
    dqcrit_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Critical humidity deficit (kg H2O per kg air)."""
    dz0v_dh_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Rate of change of vegetation roughness length for momentum with height."""
    emis_pft_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Surface emissivity of vegetated surfaces."""
    eta_sl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Live stemwood coefficient (kg C/m/(m2 leaf))."""
    f0_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """CI / CA for DQ = 0."""
    fd_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Scale factor for dark respiration."""
    fsmc_mod_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Switch for weighting soil layer contributions to soil moisture availability."""
    fsmc_of_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Moisture availability below which leaves are dropped."""
    fsmc_p0_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """PFT-dependent water stress threshold parameter."""
    g_leaf_0_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Minimum turnover rate for leaves (/360days)."""
    glmin_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Minimum leaf conductance for H2O."""
    gsoil_f_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Soil conductance enhancement factor."""
    hw_sw_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of N stem to N heartwood (kgN/kgN)."""
    infil_f_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Infiltration enhancement factor."""
    kext_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Light extinction coefficient for Beer's Law."""
    kn_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Parameter for decay of nitrogen through canopy by layers."""
    knl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Parameter for decay of nitrogen through canopy by LAI."""
    kpar_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """PAR Extinction coefficient."""
    lai_alb_lim_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Minimum LAI in albedo calculation without snow."""
    lma_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Leaf mass per unit area."""
    neff_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Scale factor relating Vcmax with leaf nitrogen concentration."""
    nl0_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Top leaf nitrogen concentration (kg N/kg C)."""
    nmass_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Top leaf nitrogen content per unit mass."""
    nr_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Root nitrogen concentration (kgN/kgC)."""
    nr_nl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of root nitrogen to leaf nitrogen concentration."""
    ns_nl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of stem nitrogen to leaf nitrogen concentration."""
    nsw_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Stemwood nitrogen concentration (kgN/kgC)."""
    omega_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf scattering coefficient for PAR."""
    omnir_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf scattering coefficient for NIR."""
    q10_leaf_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Q10 factor for plant respiration."""
    r_grow_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Growth respiration fraction."""
    rootd_ft_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Parameter determining root depth (m)."""
    sigl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Specific density of leaf carbon (kg C/m2 leaf)."""
    tleaf_of_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Temperature below which leaves are dropped."""
    tlow_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Lower temperature parameter for photosynthesis."""
    tupp_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Upper temperature parameter for photosynthesis."""
    vint_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Y-intercept in linear regression between Vcmax and Narea."""
    vsl_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Slope in linear regression between Vcmax and Narea."""
    z0hm_classic_pft_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Roughness length ratio for heat/momentum for CLASSIC."""
    z0hm_pft_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of roughness length for heat to momentum."""


class PftParamsNamelist(NamelistModel):
    """Top-level schema for ``pft_params.nml``."""

    jules_pftparm: JulesPftparm
