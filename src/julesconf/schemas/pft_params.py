"""Validation schema for ``pft_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/pft_params.nml.rst``

All list fields have length ``npft`` (cross-namelist; validated in
:class:`~julesconf.schemas.namelists.JulesNamelists`).
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["PftParamsNamelist"]


class JulesPftparm(BaseModel):
    """``JULES_PFTPARM`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    canht_ft_io: list[float] | None = None
    """The height of each PFT (m), also known as the canopy height."""
    lai_io: list[float] | None = None
    """The leaf area index (LAI) of each PFT."""
    c3_io: list[int] | None = None
    """Flag indicating whether PFT is C3 type."""
    orient_io: list[int] | None = None
    """Flag indicating leaf angle distribution."""
    can_struct_a_io: list[float] | None = None
    """Canopy structure factor (dimensionless)."""
    a_wl_io: list[float] | None = None
    """Allometric coefficient relating target woody biomass to leaf area index."""
    a_ws_io: list[float] | None = None
    """Woody biomass as a multiple of live stem biomass."""
    albsnc_max_io: list[float] | None = None
    """Snow-covered albedo for large leaf area index."""
    albsnc_min_io: list[float] | None = None
    """Snow-covered albedo for zero leaf area index."""
    albsnf_max_io: list[float] | None = None
    """Snow-free albedo for large LAI."""
    albsnf_maxu_io: list[float] | None = None
    """Upper bound for snow-free albedo for large LAI when scaled."""
    albsnf_maxl_io: list[float] | None = None
    """Lower bound for snow-free albedo for large LAI when scaled."""
    alnir_io: list[float] | None = None
    """Leaf reflection coefficient for NIR."""
    alpar_io: list[float] | None = None
    """Leaf reflection coefficient for VIS (photosynthetically active radiation)."""
    alpha_io: list[float] | None = None
    """Quantum efficiency of photosynthesis (mol CO2 per mol PAR photons)."""
    b_wl_io: list[float] | None = None
    """Allometric exponent relating target woody biomass to leaf area index."""
    catch0_io: list[float] | None = None
    """Minimum canopy capacity (kg m⁻²)."""
    dcatch_dlai_io: list[float] | None = None
    """Rate of change of canopy capacity with LAI."""
    dgl_dm_io: list[float] | None = None
    """Rate of change of leaf turnover rate with moisture availability."""
    dgl_dt_io: list[float] | None = None
    """Rate of change of leaf turnover rate with temperature."""
    dqcrit_io: list[float] | None = None
    """Critical humidity deficit (kg H2O per kg air)."""
    dz0v_dh_io: list[float] | None = None
    """Rate of change of vegetation roughness length for momentum with height."""
    emis_pft_io: list[float] | None = None
    """Surface emissivity of vegetated surfaces."""
    eta_sl_io: list[float] | None = None
    """Live stemwood coefficient (kg C/m/(m2 leaf))."""
    f0_io: list[float] | None = None
    """CI / CA for DQ = 0."""
    fd_io: list[float] | None = None
    """Scale factor for dark respiration."""
    fsmc_mod_io: list[int] | None = None
    """Switch for weighting soil layer contributions to soil moisture availability."""
    fsmc_of_io: list[float] | None = None
    """Moisture availability below which leaves are dropped."""
    fsmc_p0_io: list[float] | None = None
    """PFT-dependent water stress threshold parameter."""
    g_leaf_0_io: list[float] | None = None
    """Minimum turnover rate for leaves (/360days)."""
    glmin_io: list[float] | None = None
    """Minimum leaf conductance for H2O."""
    gsoil_f_io: list[float] | None = None
    """Soil conductance enhancement factor."""
    hw_sw_io: list[float] | None = None
    """Ratio of N stem to N heartwood (kgN/kgN)."""
    infil_f_io: list[float] | None = None
    """Infiltration enhancement factor."""
    kext_io: list[float] | None = None
    """Light extinction coefficient for Beer's Law."""
    kn_io: list[float] | None = None
    """Parameter for decay of nitrogen through canopy by layers."""
    knl_io: list[float] | None = None
    """Parameter for decay of nitrogen through canopy by LAI."""
    kpar_io: list[float] | None = None
    """PAR Extinction coefficient."""
    lai_alb_lim_io: list[float] | None = None
    """Minimum LAI in albedo calculation without snow."""
    lma_io: list[float] | None = None
    """Leaf mass per unit area."""
    neff_io: list[float] | None = None
    """Scale factor relating Vcmax with leaf nitrogen concentration."""
    nl0_io: list[float] | None = None
    """Top leaf nitrogen concentration (kg N/kg C)."""
    nmass_io: list[float] | None = None
    """Top leaf nitrogen content per unit mass."""
    nr_io: list[float] | None = None
    """Root nitrogen concentration (kgN/kgC)."""
    nr_nl_io: list[float] | None = None
    """Ratio of root nitrogen to leaf nitrogen concentration."""
    ns_nl_io: list[float] | None = None
    """Ratio of stem nitrogen to leaf nitrogen concentration."""
    nsw_io: list[float] | None = None
    """Stemwood nitrogen concentration (kgN/kgC)."""
    omega_io: list[float] | None = None
    """Leaf scattering coefficient for PAR."""
    omnir_io: list[float] | None = None
    """Leaf scattering coefficient for NIR."""
    q10_leaf_io: list[float] | None = None
    """Q10 factor for plant respiration."""
    r_grow_io: list[float] | None = None
    """Growth respiration fraction."""
    rootd_ft_io: list[float] | None = None
    """Parameter determining root depth (m)."""
    sigl_io: list[float] | None = None
    """Specific density of leaf carbon (kg C/m2 leaf)."""
    tleaf_of_io: list[float] | None = None
    """Temperature below which leaves are dropped."""
    tlow_io: list[float] | None = None
    """Lower temperature parameter for photosynthesis."""
    tupp_io: list[float] | None = None
    """Upper temperature parameter for photosynthesis."""
    vint_io: list[float] | None = None
    """Y-intercept in linear regression between Vcmax and Narea."""
    vsl_io: list[float] | None = None
    """Slope in linear regression between Vcmax and Narea."""
    z0hm_classic_pft_io: list[float] | None = None
    """Roughness length ratio for heat/momentum for CLASSIC."""
    z0hm_pft_io: list[float] | None = None
    """Ratio of roughness length for heat to momentum."""


class PftParamsNamelist(BaseModel):
    """Top-level schema for ``pft_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_pftparm: JulesPftparm
