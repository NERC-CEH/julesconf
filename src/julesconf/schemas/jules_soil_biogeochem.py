"""Validation schema for ``jules_soil_biogeochem.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_soil_biogeochem.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["JulesSoilBiogeochemNamelist"]


class JulesSoilBiogeochem(BaseModel):
    """``JULES_SOIL_BIOGEOCHEM`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    soil_bgc_model: int = Field(default=1, ge=1, le=3)

    # Parameters for all models
    q10_soil: float = 2.0

    # Single-pool model parameters (soil_bgc_model = 1)
    kaps: float = 0.5e-8

    # Single-pool and 4-pool parameters (soil_bgc_model = 1 or 2)
    l_q10: bool = True
    l_soil_resp_lev2: bool = False

    # 4-pool model parameters (soil_bgc_model = 2)
    l_layeredc: bool = False
    l_label_frac_cs: bool = False
    kaps_4pool: list[float] | None = None  # length 4
    bio_hum_cn: float = 10.0
    sorp: float = 10.0
    n_inorg_turnover: float = 1.0
    tau_resp: float = 2.0
    diff_n_pft: float = 5.0
    z_burn_max: float = 0.2

    # 4-pool or ECOSSE (soil_bgc_model = 2 or 3)
    tau_lit: float = 5.0

    # Methane parameters
    l_ch4_tlayered: bool = False
    l_ch4_interactive: bool = False
    l_ch4_microbe: bool = False
    ch4_substrate: int = Field(default=1, ge=1, le=3)
    t0_ch4: float = 273.15
    const_ch4_cs: float = 7.41e-12
    q10_ch4_cs: float = 3.7
    const_ch4_npp: float = 9.99e-3
    q10_ch4_npp: float = 1.5
    const_ch4_resps: float = 4.36e-3
    q10_ch4_resps: float = 1.5
    ch4_cpow: float = 1.0
    tau_ch4: float = 6.5

    # Microbial methane parameters (only if l_ch4_microbe = True)
    k2_ch4: float = 0.01
    kd_ch4: float = 0.0003
    rho_ch4: float = 47.0
    q10_mic_ch4: float = 4.3
    cue_ch4: float = 0.03
    mu_ch4: float = 0.00042
    frz_ch4: float = 0.5
    alpha_ch4: float = 0.001
    ev_ch4: float = 5.0
    q10_ev_ch4: float = 2.2


class JulesSoilBiogeochemNamelist(BaseModel):
    """Top-level schema for ``jules_soil_biogeochem.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_soil_biogeochem: JulesSoilBiogeochem = JulesSoilBiogeochem()
