"""Validation schema for `jules_soil_biogeochem.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_soil_biogeochem.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import name_or_value

__all__ = [
    "Ch4Substrate",
    "JulesSoilBiogeochem",
    "JulesSoilBiogeochemNamelist",
    "SoilBgcModel",
]


class SoilBgcModel(IntEnum):
    """Soil biogeochemistry model choice (`soil_bgc_model`)."""

    single_pool = 1
    four_pool = 2
    ecosse = 3


class Ch4Substrate(IntEnum):
    """Substrate used for wetland methane emissions (`ch4_substrate`)."""

    soil_carbon = 1
    npp = 2
    soil_respiration = 3


class JulesSoilBiogeochem(NamelistModel):
    """`JULES_SOIL_BIOGEOCHEM` namelist members."""

    soil_bgc_model: Annotated[SoilBgcModel, name_or_value(SoilBgcModel)] = (
        SoilBgcModel.single_pool
    )
    """Choice for model of soil biogeochemistry: `single_pool` (1), `four_pool` (2), `ecosse` (3)."""

    # Parameters for all models
    q10_soil: float = 2.0
    """Q10 factor for soil respiration."""

    # Single-pool model parameters (soil_bgc_model = 1)
    kaps: float = 0.5e-8
    """Specific soil respiration rate at 25 degC and optimum soil moisture (s⁻¹)."""

    # Single-pool and 4-pool parameters (soil_bgc_model = 1 or 2)
    l_q10: bool = True
    """Switch for use of Q10 approach when calculating soil respiration."""
    l_soil_resp_lev2: bool = False
    """Switch affecting the temperature and moisture used for soil respiration calculation."""

    # 4-pool model parameters (soil_bgc_model = 2)
    l_layeredc: bool = False
    """Switch for using the layered soil carbon model."""
    l_label_frac_cs: bool = False
    """Switch for labelling and tracing a subset of the layered soil carbon."""
    kaps_4pool: Annotated[list[float], Field(min_length=4, max_length=4)] | None = None
    """Specific soil respiration rate for the 4-pool submodel for each soil carbon pool."""
    bio_hum_cn: float = 10.0
    """Parameter controlling ratio of C to N for BIO and HUM pools."""
    sorp: float = 10.0
    """Parameter controlling the leaching of inorganic N through the soil profile."""
    n_inorg_turnover: float = 1.0
    """Parameter controlling the lifetime of the inorganic N pool."""
    tau_resp: float = 2.0
    """Parameter controlling decay of respiration with depth (m⁻¹)."""
    diff_n_pft: float = 5.0
    """Parameter controlling the rate of re-filling of the available inorganic nitrogen pool."""
    z_burn_max: float = 0.2
    """Parameter controlling the depth to which fire burns soil litter carbon."""

    # 4-pool or ECOSSE (soil_bgc_model = 2 or 3)
    tau_lit: float = 5.0
    """Parameter controlling the decay of litter with depth (m⁻¹)."""

    # Methane parameters
    l_ch4_tlayered: bool = False
    """Switch to calculate methane emissions based on layered soil temperature."""
    l_ch4_interactive: bool = False
    """Switch to couple the methane emission into the carbon cycle."""
    l_ch4_microbe: bool = False
    """Switch to enable the microbial methane production scheme."""
    ch4_substrate: Annotated[Ch4Substrate, name_or_value(Ch4Substrate)] = (
        Ch4Substrate.soil_carbon
    )
    """Choice of substrate for wetland methane: `soil_carbon` (1), `npp` (2), `soil_respiration` (3)."""
    t0_ch4: float = 273.15
    """Reference temperature for the Q10 function CH4 emission calculation."""
    const_ch4_cs: float = 7.41e-12
    """Scale factor for wetland CH4 emissions when soil carbon is the substrate."""
    q10_ch4_cs: float = 3.7
    """Q10 value for wetland CH4 emissions when soil carbon is the substrate."""
    const_ch4_npp: float = 9.99e-3
    """Scale factor for wetland CH4 emissions when NPP is the substrate."""
    q10_ch4_npp: float = 1.5
    """Q10 value for wetland CH4 emissions when NPP is the substrate."""
    const_ch4_resps: float = 4.36e-3
    """Scale factor for wetland CH4 emissions when soil respiration is the substrate."""
    q10_ch4_resps: float = 1.5
    """Q10 value for wetland CH4 emissions when soil respiration is the substrate."""
    ch4_cpow: float = 1.0
    """Power of soil carbon used to calculate methane emissions."""
    tau_ch4: float = 6.5
    """Exponent in the exponential decline of methane emissions with soil depth."""

    # Microbial methane parameters (only if l_ch4_microbe = True)
    k2_ch4: float = 0.01
    """Baseline methanogenic respiration rate (hr⁻¹)."""
    kd_ch4: float = 0.0003
    """Baseline methanogenic mortality rate (hr⁻¹)."""
    rho_ch4: float = 47.0
    """Factor in substrate limitation function for methanogenic respiration."""
    q10_mic_ch4: float = 4.3
    """Q10 factor for methanogens."""
    cue_ch4: float = 0.03
    """Carbon use efficiency of methanogenic growth."""
    mu_ch4: float = 0.00042
    """Threshold growth rate below which methanogens die (hr⁻¹)."""
    frz_ch4: float = 0.5
    """Factor to reduce CH4 substrate production when soil is sufficiently frozen."""
    alpha_ch4: float = 0.001
    """Ratio between maintenance and growth respiration rates for methanogens."""
    ev_ch4: float = 5.0
    """Timescale over which methanogenic traits adapt to temperature change."""
    q10_ev_ch4: float = 2.2
    """Q10 for temperature response of methanogenic traits under adaptation."""


class JulesSoilBiogeochemNamelist(NamelistModel):
    """Top-level schema for `jules_soil_biogeochem.nml`."""

    jules_soil_biogeochem: JulesSoilBiogeochem = JulesSoilBiogeochem()
