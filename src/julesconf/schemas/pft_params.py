"""Validation schema for `pft_params.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/pft_params.nml.rst`

All list fields have length `npft` (cross-namelist; validated in
`julesconf.schemas.JulesNamelists`).
"""

from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import Fraction, ListLen, NonNegFloat, ZeroOne

__all__ = ["JulesPftparm", "PftParamsNamelist"]


class JulesPftparm(NamelistModel):
    """`JULES_PFTPARM` namelist members."""

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
    nr_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Root nitrogen concentration (kgN/kgC).

    Only used with `JULES_VEGETATION::l_trait_phys` = T. Unbounded: the user
    guide gives no permitted range and the vn7.9 rose metadata gives no
    `range`, and shipped trait-physiology configurations use `-1` to mark a
    PFT for which the concentration is derived rather than prescribed.
    """
    nr_nl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of root nitrogen to leaf nitrogen concentration."""
    ns_nl_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ratio of stem nitrogen to leaf nitrogen concentration."""
    nsw_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Stemwood nitrogen concentration (kgN/kgC).

    Unbounded for the same reason as `nr_io`, and carries the same `-1`
    sentinel in the shipped trait-physiology configurations.
    """
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

    # --- BVOC emissions (JULES_VEGETATION::l_bvoc_emis) ---
    ief_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Isoprene emission factor per PFT (µgC g⁻¹ h⁻¹)."""
    tef_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """(Mono-)terpene emission factor per PFT (µgC g⁻¹ h⁻¹)."""
    mef_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Methanol emission factor per PFT (µgC g⁻¹ h⁻¹)."""
    aef_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Acetone emission factor per PFT (µgC g⁻¹ h⁻¹)."""
    ci_st_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Leaf-internal CO₂ concentration at standard conditions (Pa)."""
    gpp_st_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Gross primary production at standard conditions (kgC m⁻² s⁻¹)."""

    # --- INFERNO interactive fire (JULES_VEGETATION::l_inferno) ---
    avg_ba_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Average burnt area on the PFT per fire event (m²)."""
    ccleaf_min_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf minimum combustion completeness."""
    ccleaf_max_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Leaf maximum combustion completeness."""
    ccwood_min_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Wood minimum combustion completeness."""
    ccwood_max_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Wood maximum combustion completeness."""
    fef_co2_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Carbon dioxide (CO₂) emission factor from natural fires (g kg⁻¹)."""
    fef_co_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Carbon monoxide (CO) emission factor from natural fires (g kg⁻¹)."""
    fef_ch4_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Methane (CH₄) emission factor from natural fires (g kg⁻¹)."""
    fef_nox_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Nitrogen oxides (NOx) emission factor from natural fires (g kg⁻¹)."""
    fef_so2_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Sulphur dioxide (SO₂) emission factor from natural fires (g kg⁻¹)."""
    fef_oc_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Organic carbon (OC) emission factor from natural fires (g kg⁻¹)."""
    fef_bc_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Black carbon (BC) emission factor from natural fires (g kg⁻¹)."""
    fef_c2h4_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ethene (C₂H₄) emission factor from natural fires (g kg⁻¹)."""
    fef_c2h6_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ethane (C₂H₆) emission factor from natural fires (g kg⁻¹)."""
    fef_c3h8_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Propane (C₃H₈) emission factor from natural fires (g kg⁻¹)."""
    fef_hcho_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Formaldehyde (HCHO) emission factor from natural fires (g kg⁻¹)."""
    fef_mecho_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Acetaldehyde (MeCHO) emission factor from natural fires (g kg⁻¹)."""
    fef_nh3_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Ammonia (NH₃) emission factor from natural fires (g kg⁻¹)."""
    fef_dms_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Dimethyl sulfide (DMS) emission factor from natural fires (g kg⁻¹)."""
    fire_mort_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Scaling factor for vegetation mortality caused by fire, from INFERNO burned area.

    `0.0` is no mortality and `1.0` is 100% mortality.
    """

    # --- Scaled albedo limits (JULES_RADIATION::l_albedo_obs) ---
    alnirl_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Lower limit on `alnir_io`, the leaf reflection coefficient for NIR."""
    alniru_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Upper limit on `alnir_io`, the leaf reflection coefficient for NIR."""
    alparl_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Lower limit on `alpar_io`, the leaf reflection coefficient for VIS.

    Unbounded, unlike its three siblings: the vn7.9 rose metadata gives
    `alnirl_io`, `alniru_io` and `alparu_io` `range=0:1` and gives this member no
    `range` at all, and the user guide states no permitted range for any of the
    four.
    """
    alparu_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Upper limit on `alpar_io`, the leaf reflection coefficient for VIS."""
    omegal_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Lower limit on `omega_io`, the leaf scattering coefficient for PAR."""
    omegau_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Upper limit on `omega_io`, the leaf scattering coefficient for PAR."""
    omnirl_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Lower limit on `omnir_io`, the leaf scattering coefficient for NIR."""
    omniru_io: Annotated[list[Fraction] | None, ListLen("npft")] = None
    """Upper limit on `omnir_io`, the leaf scattering coefficient for NIR."""

    # --- Farquhar photosynthesis (JULES_VEGETATION::photo_model = 2) ---
    act_jmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Activation energy for the temperature response of Jmax (J mol⁻¹).

    Used when `JULES_VEGETATION::photo_act_model` = 1; `JULES_VEGETATION::act_j_coef`
    replaces it when that switch is 2.
    """
    act_vcmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Activation energy for the temperature response of Vcmax (J mol⁻¹).

    Used when `JULES_VEGETATION::photo_act_model` = 1; `JULES_VEGETATION::act_v_coef`
    replaces it when that switch is 2.
    """
    deact_jmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Deactivation energy for the temperature response of Jmax (J mol⁻¹).

    Describes the rate of decrease above the optimum temperature.
    """
    deact_vcmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Deactivation energy for the temperature response of Vcmax (J mol⁻¹).

    Describes the rate of decrease above the optimum temperature.
    """
    alpha_elec_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Quantum yield of electron transport (mol electrons per mol PAR photons)."""
    jv25_ratio_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Ratio of Jmax to Vcmax at 25 °C (mol electrons per mol CO₂).

    `JULES_VEGETATION::jv25_coef` replaces it under thermal
    adaptation/acclimation; with `JULES_VEGETATION::photo_jv_model` = 2 it is
    combined with `n_alloc_jmax` and `n_alloc_vcmax` instead.
    """
    ds_jmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Entropy factor for the temperature response of Jmax (J mol⁻¹ K⁻¹).

    Only used when acclimation is off (`JULES_VEGETATION::photo_acclim_model` = 0);
    `JULES_VEGETATION::dsj_coef` replaces it otherwise.
    """
    ds_vcmax_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Entropy factor for the temperature response of Vcmax (J mol⁻¹ K⁻¹).

    Only used when acclimation is off (`JULES_VEGETATION::photo_acclim_model` = 0);
    `JULES_VEGETATION::dsv_coef` replaces it otherwise.
    """

    # --- Stomatal conductance (JULES_VEGETATION::stomata_model) ---
    g1_stomata_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Parameter g1 of the Medlyn et al. (2011) stomatal conductance model (kPa^0.5).

    Only used with `JULES_VEGETATION::stomata_model` = 2.
    """
    sox_a_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Shape parameter in the xylem vulnerability curve.

    Only used with the SOX model (`JULES_VEGETATION::stomata_model` = 3).
    """
    sox_p50_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Xylem water potential at which xylem hydraulic conductance is halved (MPa).

    Only used with the SOX model (`JULES_VEGETATION::stomata_model` = 3).
    """
    sox_rp_min_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Plant minimum hydraulic resistance (m² s MPa mol⁻¹).

    Only used with the SOX model (`JULES_VEGETATION::stomata_model` = 3).
    """

    # --- SUGAR carbohydrate model (JULES_VEGETATION::l_sugar) ---
    sug_g0_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Specific structural carbon production rate (kg C m⁻² s⁻¹)."""
    sug_grec_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Specific structural carbon recycling rate (kg C m⁻² s⁻¹)."""
    sug_yg_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Growth yield for the SUGAR model."""

    # --- Ozone damage (JULES_VEGETATION::l_o3_damage) ---
    fl_o3_ct_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Critical flux of O₃ to vegetation (nmol m⁻² s⁻¹)."""
    dfp_dcuo_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Plant-type-specific O₃ sensitivity parameter (nmol⁻¹ m² s)."""

    # --- Soil moisture stress from soil potential ---
    psi_open_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Soil potential above which the soil moisture stress factor is one (Pa).

    Only used with `JULES_VEGETATION::l_use_pft_psi` = T. Unbounded: the user
    guide says "must be negative", but the vn7.9 rose metadata gives no `range`
    and shipped configurations set it to `0`.
    """
    psi_close_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Soil potential below which the soil moisture stress factor is zero (Pa).

    Only used with `JULES_VEGETATION::l_use_pft_psi` = T. Unbounded for the same
    reason as `psi_open_io`.
    """

    # --- Miscellaneous ---
    z0v_io: Annotated[list[float] | None, ListLen("npft")] = None
    """Specified vegetation roughness length for momentum (m).

    Used when `JULES_VEGETATION::l_spec_veg_z0` = T; `dz0v_dh_io` is used
    instead when it is F.
    """
    dust_veg_scj_io: Annotated[list[NonNegFloat] | None, ListLen("npft")] = None
    """Dust emissions scaling factor per PFT. Not applicable to JULES standalone."""


class PftParamsNamelist(NamelistModel):
    """Top-level schema for `pft_params.nml`."""

    jules_pftparm: JulesPftparm
