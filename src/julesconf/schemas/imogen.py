"""Validation schema for `imogen.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/imogen.nml.rst`
"""

from enum import IntEnum
from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if
from julesconf.schemas.constraints import Fraction, name_or_value

__all__ = [
    "ChangeMetdataMethod",
    "ImogenAnlgValsList",
    "ImogenNamelist",
    "ImogenOnoffSwitch",
    "ImogenRunList",
]


class ChangeMetdataMethod(IntEnum):
    """Method used to change the driving data over time (`change_metdata_method`)."""

    analogue_patterns = 1
    prescribed_anomalies = 2
    global_temperature_patterns = 3


class ImogenOnoffSwitch(NamelistModel):
    """`IMOGEN_ONOFF_SWITCH` namelist members."""

    l_imogen: bool = False
    """Switch for IMOGEN."""
    l_daily_metdata_climatol: bool = False
    """The driving climatology is supplied as daily data on a 360-day calendar.

    When FALSE it is supplied as monthly data.
    """


class ImogenRunList(NamelistModel):
    """`IMOGEN_RUN_LIST` namelist members."""

    co2_init_ppmv: float = 286.085
    """Initial CO2 concentration (ppmv)."""
    file_scen_emits: str | None = None
    """The file containing CO2 emissions, in the format of the IMOGEN example."""
    file_non_co2_radf: str | None = None
    """The file containing non-CO2 radiative forcing values, in the format of the IMOGEN example."""
    nyr_non_co2: int = Field(default=21, ge=0)
    """The number of years for which non-CO2 forcing is prescribed."""
    file_scen_co2_ppmv: str | None = None
    """The file containing CO2 concentrations (ppmv), in the format of the IMOGEN example."""
    ch4_init_ppbv: float = 774.1
    """Initial CH4 concentration (ppbv). Only used when `land_feed_ch4` is TRUE."""
    yr_fch4_ref: int = Field(default=2000, ge=0)
    """The reference year for wetland CH4 emissions and the atmospheric CH4 decay rate.

    Gives the year `fch4_ref`, `tau_ch4_ref` and `ch4_ppbv_ref` describe. Only
    used when `land_feed_ch4` is TRUE.

    Typed `integer` by the rose metadata and `real` by the user guide; julesconf
    follows the metadata.
    """
    ch4_ppbv_ref: float = 1751.02
    """Atmospheric CH4 concentration at `yr_fch4_ref` (ppbv).

    Only used when `land_feed_ch4` is TRUE.
    """
    tau_ch4_ref: float = 8.4
    """Lifetime of CH4 in the atmosphere at `yr_fch4_ref` (years).

    Only used when `land_feed_ch4` is TRUE.
    """
    fch4_ref: float = 180.0
    """Reference global wetland CH4 flux for `yr_fch4_ref` (Tg CH4 yr⁻¹).

    Only used when `land_feed_ch4` is TRUE.
    """
    file_ch4_n2o: str | None = None
    """The file containing atmospheric CH4 and N2O concentrations.

    An ASCII file with no header and one row per year, holding the year, the
    CH4 concentration (ppbv) and the N2O concentration (ppbv). The number of
    rows is `nyr_ch4_n2o`. Only used when `land_feed_ch4` is TRUE.
    """
    nyr_ch4_n2o: int = Field(default=241, ge=0)
    """The number of years of CH4 and N2O data in `file_ch4_n2o`.

    Only used when `land_feed_ch4` is TRUE.
    """
    l_change_metdata: bool = True
    """Allow the driving meteorological data to change over time.

    The way it changes is set by `change_metdata_method`.
    """
    change_metdata_method: (
        Annotated[ChangeMetdataMethod, name_or_value(ChangeMetdataMethod)] | None
    ) = None
    """How the driving data is allowed to change over time.

    `analogue_patterns` (1) drives JULES from the analogue model and spatial
    patterns of sensitivity to global mean temperature change;
    `prescribed_anomalies` (2) uses a prescribed time series of anomalies;
    `global_temperature_patterns` (3) uses a prescribed global mean temperature
    change with the climate patterns. Only used when `l_change_metdata` is TRUE.
    """
    c_emissions: bool = True
    """Calculate the CO2 concentration from anthropogenic emissions."""
    include_co2: bool = True
    """Include adjustments to CO2 values."""
    include_non_co2_radf: bool = True
    """Include adjustments to non-CO2 radiative forcing."""
    land_feed_co2: bool = False
    """Include land CO2 feedbacks on atmospheric CO2."""
    land_feed_ch4: bool = False
    """Include wetland CH4 feedbacks on atmospheric CH4.

    The constant wetland CH4 emissions are perturbed by the anomaly in the
    modelled natural wetland CH4 emission, which is diagnosed over the wetland
    area when `JULES_HYDROLOGY::l_top` is TRUE. The model must be calibrated to
    produce `fch4_ref` in `yr_fch4_ref`; see the user guide.
    """
    ocean_feed: bool = False
    """Include ocean feedbacks on atmospheric CO2."""
    initial_co2_ch4_year: int | None = None
    """The initial year for the ocean CO2 accumulation. Only used when `ocean_feed` is TRUE."""
    nyr_emiss: int = Field(default=241, ge=0)
    """The number of years of emissions data in `file_scen_emits`."""
    initialise_from_dump: bool = False
    """Initialise the IMOGEN prognostics from `dump_file` rather than internally."""
    dump_file: str | None = None
    """The dump file to initialise from. Only used when `initialise_from_dump` is TRUE."""

    _FEEDBACK_SWITCHES: ClassVar[tuple[str, ...]] = (
        "land_feed_co2",
        "ocean_feed",
        "land_feed_ch4",
        "c_emissions",
        "include_non_co2_radf",
    )
    """The switches neither prescribed-data method supports.

    Transcribed from the ten `namelist:imogen_run_list=change_metdata_method`
    `fail-if` rules in the JULES vn7.9 rose metadata — five switches by the two
    methods that reject them. Methods 2 and 3 both take the CO2 concentration
    as given, so a feedback that would change it has nothing to act on
    (`imogen.nml.rst`: "Currently no feedbacks included").
    """

    @model_validator(mode="after")
    def _check_metdata_method_feedbacks(self) -> "ImogenRunList":
        """Reject feedback switches the prescribed-data methods cannot honour."""
        method = self.change_metdata_method
        if method is not None and method in (
            ChangeMetdataMethod.prescribed_anomalies,
            ChangeMetdataMethod.global_temperature_patterns,
        ):
            for switch in self._FEEDBACK_SWITCHES:
                fail_if(
                    getattr(self, switch),
                    f"{switch} is not available when change_metdata_method is"
                    f" {method.name} ({method.value})",
                )
        return self


class ImogenAnlgValsList(NamelistModel):
    """`IMOGEN_ANLG_VALS_LIST` namelist members."""

    diff_frac_const_imogen: Fraction = 0.4
    """Fraction of downward shortwave radiation assumed to be diffuse.

    IMOGEN uses this in place of `JULES_DRIVE::diff_frac_const`.
    """
    q2co2: float = 3.74
    """Radiative forcing due to doubling CO2 (W m⁻²)."""
    f_ocean: float = 0.711
    """Fractional coverage of the ocean."""
    kappa_o: float = 383.8
    """Ocean eddy diffusivity (W m⁻¹ K⁻¹)."""
    lambda_l: float = 0.52
    """Inverse of the climate sensitivity over land (W m⁻² K⁻¹)."""
    lambda_o: float = 1.75
    """Inverse of the climate sensitivity over ocean (W m⁻² K⁻¹)."""
    mu: float = 1.87
    """Ratio of land to ocean temperature anomalies."""
    t_ocean_init: float = 289.28
    """Initial ocean temperature (K)."""
    file_patt: str | None = None
    """The NetCDF file containing the GCM patterns.

    Monthly data (12 months) with the dimension `imogen_drive` representing time.
    """
    file_clim: str | None = None
    """The NetCDF file containing the initialising climatology.

    Monthly data (12 months) with the dimension `imogen_drive` representing time.
    """
    file_base_anom: str | None = None
    """The stem of the NetCDF files containing prescribed anomalies.

    One file per year, named `file_base_anom` followed by a four-digit year and
    `.nc`.
    """


class ImogenNamelist(NamelistModel):
    """Top-level schema for `imogen.nml`."""

    imogen_onoff_switch: ImogenOnoffSwitch = ImogenOnoffSwitch()
    imogen_run_list: ImogenRunList = ImogenRunList()
    imogen_anlg_vals_list: ImogenAnlgValsList = ImogenAnlgValsList()
