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
    lai_io: list[float] | None = None
    c3_io: list[int] | None = None
    orient_io: list[int] | None = None
    can_struct_a_io: list[float] | None = None
    a_wl_io: list[float] | None = None
    a_ws_io: list[float] | None = None
    albsnc_max_io: list[float] | None = None
    albsnc_min_io: list[float] | None = None
    albsnf_max_io: list[float] | None = None
    albsnf_maxu_io: list[float] | None = None
    albsnf_maxl_io: list[float] | None = None
    alnir_io: list[float] | None = None
    alpar_io: list[float] | None = None
    alpha_io: list[float] | None = None
    b_wl_io: list[float] | None = None
    catch0_io: list[float] | None = None
    dcatch_dlai_io: list[float] | None = None
    dgl_dm_io: list[float] | None = None
    dgl_dt_io: list[float] | None = None
    dqcrit_io: list[float] | None = None
    dz0v_dh_io: list[float] | None = None
    emis_pft_io: list[float] | None = None
    eta_sl_io: list[float] | None = None
    f0_io: list[float] | None = None
    fd_io: list[float] | None = None
    fsmc_mod_io: list[int] | None = None
    fsmc_of_io: list[float] | None = None
    fsmc_p0_io: list[float] | None = None
    g_leaf_0_io: list[float] | None = None
    glmin_io: list[float] | None = None
    gsoil_f_io: list[float] | None = None
    hw_sw_io: list[float] | None = None
    infil_f_io: list[float] | None = None
    kext_io: list[float] | None = None
    kn_io: list[float] | None = None
    knl_io: list[float] | None = None
    kpar_io: list[float] | None = None
    lai_alb_lim_io: list[float] | None = None
    lma_io: list[float] | None = None
    neff_io: list[float] | None = None
    nl0_io: list[float] | None = None
    nmass_io: list[float] | None = None
    nr_io: list[float] | None = None
    nr_nl_io: list[float] | None = None
    ns_nl_io: list[float] | None = None
    nsw_io: list[float] | None = None
    omega_io: list[float] | None = None
    omnir_io: list[float] | None = None
    q10_leaf_io: list[float] | None = None
    r_grow_io: list[float] | None = None
    rootd_ft_io: list[float] | None = None
    sigl_io: list[float] | None = None
    tleaf_of_io: list[float] | None = None
    tlow_io: list[float] | None = None
    tupp_io: list[float] | None = None
    vint_io: list[float] | None = None
    vsl_io: list[float] | None = None
    z0hm_classic_pft_io: list[float] | None = None
    z0hm_pft_io: list[float] | None = None


class PftParamsNamelist(BaseModel):
    """Top-level schema for ``pft_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_pftparm: JulesPftparm
