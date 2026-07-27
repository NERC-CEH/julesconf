"""Validation schema for `ancillaries.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/ancillaries.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive
from julesconf.schemas.constraints import ListLen, PerElementDefault

__all__ = [
    "AncillariesNamelist",
    "JulesAgric",
    "JulesCo2",
    "JulesCropProps",
    "JulesFlake",
    "JulesFrac",
    "JulesIrrigProps",
    "JulesOverbankProps",
    "JulesPdm",
    "JulesRiversProps",
    "JulesSoilProps",
    "JulesTop",
    "JulesVegetationProps",
    "JulesWaterResourcesProps",
    "UrbanProperties",
]


def _check_nvars_lists(obj: NamelistModel, nvars_val: int) -> None:
    """Raise ValueError if any provided list has wrong length vs nvars."""
    for name in ("var", "use_file", "const_val", "var_name", "tpl_name"):
        val = getattr(obj, name, None)
        if val is not None and len(val) != nvars_val:
            raise ValueError(
                f"{name} has {len(val)} element(s), expected nvars={nvars_val}"
            )
    if nvars_val > 0 and getattr(obj, "var", None) is None:
        raise ValueError("var is required when nvars > 0")


class JulesFrac(NamelistModel):
    """`JULES_FRAC` namelist members."""

    file: str | None = None
    """The name of the file to read surface type fractional coverage data from."""
    read_from_dump: bool = False
    """Populate variables from dump file if TRUE, otherwise use other namelist members."""
    frac_name: str = "frac"
    """The name of the variable containing the surface type fractional coverage data.

    Only used for NetCDF files; in an ASCII file the coverage data is expected
    to be the first variable.
    """


class _NvarsModel(NamelistModel):
    """Mixin for namelists with nvars/var/use_file/const_val pattern."""

    nvars: int = Field(default=0, ge=0)
    """The number of vegetation property variables that will be provided."""
    var: Annotated[list[str] | None, ListLen("nvars")] = None
    """List of vegetation variable names as recognised by JULES."""
    use_file: Annotated[
        list[bool] | None, ListLen("nvars"), PerElementDefault(True, "nvars")
    ] = None
    """Indicates if variable should be read from file or set to constant value."""
    const_val: Annotated[list[float] | None, ListLen("nvars")] = None
    """Constant value that variable will be set to at every point."""
    var_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """The name of the variable in the file containing the data."""
    file: str | None = None
    """The name of the file to read surface type fractional coverage data from."""
    read_from_dump: bool = False
    """Populate variables from dump file if TRUE, otherwise use other namelist members."""
    const_z: bool = False
    """Switch indicating if soil properties are uniform with depth."""
    read_list: bool = False
    """Read a list of file names, one per line for each of `nvars`.

    Files named in the list cannot use variable name templating.
    """
    tpl_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """For each JULES variable, the string to substitute into a templated file name."""

    @model_validator(mode="after")
    def _check_lists(self) -> "_NvarsModel":
        _check_nvars_lists(self, self.nvars)
        return self


class JulesSoilProps(_NvarsModel):
    """`JULES_SOIL_PROPS` namelist members."""


class JulesTop(_NvarsModel):
    """`JULES_TOP` namelist members."""


class JulesAgric(NamelistModel):
    """`JULES_AGRIC` namelist members."""

    l_triffid_agric: bool = False
    zero_agric: bool = True
    """Set the agricultural fraction to zero at all points."""
    zero_past: bool = True
    """Set the pasture fraction to zero at all points.

    Pasture fraction is only used when `JULES_VEGETATION::l_trif_crop` is TRUE.
    """
    frac_agr: float | None = None
    """The agricultural fraction, for a single-location input grid."""
    frac_past: float | None = None
    """The pasture fraction, for a single-location input grid."""
    file: str | None = None
    """The file to read agricultural fraction data from."""
    read_from_dump: bool = False
    """Populate variables from dump file if TRUE, otherwise use other namelist members."""
    agric_name: str | None = None
    """Name in `file` of the variable holding the agricultural fraction data."""
    file_past: str | None = None
    """The file to read pasture fraction data from."""
    past_name: str | None = None
    """Name in `file_past` of the variable holding the pasture fraction data."""
    zero_biocrop: bool = True
    """Set the biocrop fraction to zero at all points.

    When FALSE the fraction comes from `frac_biocrop`, or from `biocrop_name`
    in `file_biocrop`.
    """
    frac_biocrop: float | None = None
    """The biocrop fraction, for a single-location input grid."""
    file_biocrop: str | None = None
    """The file to read biocrop fraction data from."""
    biocrop_name: str | None = None
    """Name in `file_biocrop` of the variable holding the biocrop fraction data."""
    read_harvest_doy_from_dump: bool = False
    """Read the biocrop harvest day-of-year from the dump file."""
    file_harvest_doy: str | None = None
    """The file to read the biocrop harvest day-of-year from."""
    harvest_doy_name: str | None = None
    """Name in `file_harvest_doy` of the variable holding the harvest day-of-year."""

    @model_validator(mode="after")
    def _warn_inactive_fractions(self) -> "JulesAgric":
        """Warn about the fraction members the three `zero_*` switches deactivate."""
        if self.zero_agric:
            warn_inactive(
                self,
                ("frac_agr", "file", "agric_name"),
                because="zero_agric is true",
            )
        if self.zero_past:
            warn_inactive(
                self,
                ("frac_past", "file_past", "past_name"),
                because="zero_past is true",
            )
        if self.zero_biocrop:
            warn_inactive(
                self,
                ("frac_biocrop", "file_biocrop", "biocrop_name"),
                because="zero_biocrop is true",
            )
        return self


class JulesVegetationProps(_NvarsModel):
    """`JULES_VEGETATION_PROPS` namelist members."""


class JulesPdm(_NvarsModel):
    """`JULES_PDM` namelist members."""


class JulesCropProps(_NvarsModel):
    """`JULES_CROP_PROPS` namelist members."""


class JulesIrrigProps(_NvarsModel):
    """`JULES_IRRIG_PROPS` namelist members."""

    read_file: bool = True
    """Read the irrigated fraction from `irrig_frac_file` rather than `const_frac_irr`."""
    irrig_frac_file: str | None = None
    """The file from which irrigation fractions are read, including path."""
    const_frac_irr: float | None = None
    """The constant irrigated fraction applied to all grid points."""
    const_irrfrac_irrtiles: float | None = None
    """The constant irrigated fraction applied to `JULES_IRRIG::irrigtiles`."""


class JulesRiversProps(_NvarsModel):
    """`JULES_RIVERS_PROPS` namelist members.

    The `nvars` ancillary members are inherited from the shared base. Note that
    JULES does **not** implement `read_from_dump` for this namelist
    (`ancillaries.nml.rst:1107`) and the vn7.9 rose metadata declares neither
    `read_from_dump` nor `const_z` here; both are inherited all the same, as
    they are for `JULES_PDM` and `URBAN_PROPERTIES`.

    The remaining members describe the river routing input grid and its
    relationship to the land grid.
    """

    is_climatology: Annotated[
        list[bool] | None, ListLen("nvars"), PerElementDefault(False, "nvars")
    ] = None
    """For each variable in `var`, whether its file is a 12-month climatology.

    Documented in the user guide (`ancillaries.nml.rst:1364`) as
    `logical(nvars)` but **absent from the vn7.9 rose metadata**, so the audit
    cannot see it. The gap is upstream's, not ours: `eraint_rfm_2ddata` sets it.
    """
    coordinate_file: str | None = None
    """The file to read coordinates for the river routing input grid from.

    Only used when `file` uses variable-name templating or `read_list` is TRUE,
    i.e. when the ancillary variables come from more than one file.
    """
    x_dim_name: str | None = None
    """The name of the x dimension of the river routing input grid."""
    y_dim_name: str | None = None
    """The name of the y dimension of the river routing input grid."""
    nx_rivers: int | None = Field(default=None, ge=2)
    """The size of the x dimension of the river routing input grid."""
    ny_rivers: int | None = Field(default=None, ge=2)
    """The size of the y dimension of the river routing input grid."""
    l_find_grid: bool | None = None
    """Calculate the land grid and river domain from the known land-point coordinates.

    FALSE uses `nx_land_grid`, `ny_land_grid`, `x1_land_grid` and
    `y1_land_grid` instead, which reproduces historical results but can produce
    a larger river domain than required.
    """
    land_dx: float | None = Field(default=None, gt=0)
    """The gridbox size of the 2D land grid in the x direction.

    In the same units as the model grid; see `JULES_LATLON::l_coord_latlon`.
    """
    land_dy: float | None = Field(default=None, gt=0)
    """The gridbox size of the 2D land grid in the y direction.

    In the same units as the model grid; see `JULES_LATLON::l_coord_latlon`.
    """
    nx_land_grid: int | None = Field(default=None, ge=1)
    """The size of the x dimension of the 2D land grid.

    Only used when `l_find_grid` is FALSE. Must be large enough to include
    every land point being modelled.
    """
    ny_land_grid: int | None = Field(default=None, ge=1)
    """The size of the y dimension of the 2D land grid. Only used when `l_find_grid` is FALSE."""
    x1_land_grid: float | None = None
    """The x coordinate of the first (western-most) column of the land grid.

    Only used when `l_find_grid` is FALSE.
    """
    y1_land_grid: float | None = None
    """The y coordinate of the first (southern-most) row of the land grid.

    Only used when `l_find_grid` is FALSE.
    """
    rivers_regrid: bool = False
    """Variables on the land grid must be regridded to the river routing grid.

    FALSE means the two grids are consistent and the simpler remapping is used.
    Regridding is only available for regular latitude/longitude grids.
    """
    rivers_length: float | None = None
    """The constant size of the rivers grid (m).

    Required, and greater than zero, when the coordinate system is not
    latitude/longitude. Under latitude/longitude with RFM or overbank
    inundation, a value less than or equal to zero triggers calculation from
    the latitudinal size of the gridboxes.
    """
    l_use_area: bool = False
    """Use a drainage area ancillary field to distinguish river from land points.

    Only used with RFM (`JULES_RIVERS::i_river_vn` = 2).
    """
    l_ignore_ancil_rivers_check: bool = False
    """Skip the check that the routing and coupling ancillaries are compatible."""

    @model_validator(mode="after")
    def _check_file_sources(self) -> "JulesRiversProps":
        """Check how the ancillary files are named against each other.

        Transcribes the `fail-if` rules on `coordinate_file`, `file` and
        `read_list` in the JULES vn7.9 rose metadata. Variable-name templating
        (`%vv` in `file`) and a list of files (`read_list`) are the two ways of
        spreading the ancillaries over several files, they are mutually
        exclusive, and both need `coordinate_file` to say where the grid
        coordinates come from.
        """
        templated = "%vv" in (self.file or "")
        fail_if(
            "%vv" in (self.coordinate_file or ""),
            "Coordinate file cannot contain variable name template.",
        )
        fail_if(
            templated and not self.coordinate_file,
            "If variable name templating is used, the file to read coordinates"
            " from must be specified.",
        )
        fail_if(
            self.read_list and templated,
            "Cannot use variable name templating while reading a list of files.",
        )
        fail_if(
            self.read_list and not self.coordinate_file,
            "If reading a list of files, the file to read coordinates from must"
            " be specified.",
        )
        fail_if(
            self.read_list and not self.file,
            "If reading a list of files, there has to be a file specified to read.",
        )
        return self


class JulesWaterResourcesProps(_NvarsModel):
    """`JULES_WATER_RESOURCES_PROPS` namelist members."""


class UrbanProperties(_NvarsModel):
    """`URBAN_PROPERTIES` namelist members."""


class JulesCo2(NamelistModel):
    """`JULES_CO2` namelist members."""

    co2_mmr: float = 5.241e-4
    """Concentration of atmospheric CO2 as mass mixing ratio."""
    read_from_dump: bool = False
    """Read the CO2 concentration from the dump file."""


class JulesOverbankProps(NamelistModel):
    """`JULES_OVERBANK_PROPS` namelist members."""


class JulesFlake(_NvarsModel):
    """`JULES_FLAKE` namelist members."""

    const_val: Annotated[
        list[float] | None, ListLen("nvars"), PerElementDefault(5.0, "nvars")
    ] = None
    """For each variable where use_file = FALSE, a constant value used everywhere.

    Unlike the other `nvars` blocks, `JULES_FLAKE` documents a default for this
    member (5.0 m lake depth), so it is overridden here rather than inherited
    from `_NvarsModel`.
    """


class AncillariesNamelist(NamelistModel):
    """Top-level schema for `ancillaries.nml`."""

    jules_frac: JulesFrac = JulesFrac()
    jules_vegetation_props: JulesVegetationProps = JulesVegetationProps()
    jules_soil_props: JulesSoilProps = JulesSoilProps()
    jules_top: JulesTop = JulesTop()
    jules_pdm: JulesPdm = JulesPdm()
    jules_agric: JulesAgric = JulesAgric()
    jules_crop_props: JulesCropProps = JulesCropProps()
    jules_irrig_props: JulesIrrigProps = JulesIrrigProps()
    jules_rivers_props: JulesRiversProps = JulesRiversProps()
    jules_water_resources_props: JulesWaterResourcesProps = JulesWaterResourcesProps()
    urban_properties: UrbanProperties = UrbanProperties()
    jules_co2: JulesCo2 = JulesCo2()
    jules_overbank_props: JulesOverbankProps = JulesOverbankProps()
    jules_flake: JulesFlake = JulesFlake()
