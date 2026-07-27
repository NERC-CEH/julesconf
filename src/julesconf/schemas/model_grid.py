"""Validation schema for `model_grid.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/model_grid.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if, warn_inactive
from julesconf.schemas.constraints import ListLen, PerElementDefault

__all__ = [
    "JulesInputGrid",
    "JulesLandFrac",
    "JulesLatlon",
    "JulesModelGrid",
    "JulesNlsizes",
    "JulesSurfHgt",
    "JulesZLand",
    "ModelGridNamelist",
]


class JulesInputGrid(NamelistModel):
    """`JULES_INPUT_GRID` namelist members."""

    grid_is_1d: bool = False
    """Indicates if the input grid is 1D or 2D."""
    nx: int = Field(default=1, ge=1)
    """The size of the x dimension."""
    ny: int = Field(default=1, ge=1)
    """The size of the y dimension."""
    dim_name: str = "land"
    grid_dim_name: str = "land"
    """The name of the single grid dimension. Only used when `grid_is_1d` = TRUE."""
    npoints: int = Field(default=0, ge=0)
    """The size of the single grid dimension. Only used when `grid_is_1d` = TRUE."""
    x_dim_name: str = "x"
    """The name of the x dimension."""
    y_dim_name: str = "y"
    """The name of the y dimension."""
    time_dim_name: str = "time"
    """The name of the time dimension in any input files containing time varying data."""
    land_frac_name: str = "land_frac"
    """The name of the variable containing the land fraction data."""
    lat_name: str = "latitude"
    lon_name: str = "longitude"

    # --- Names of the extra dimensions variables may carry ---
    # For ASCII files these are arbitrary; for NetCDF files they must match the
    # dimension names in the input file(s).
    pft_dim_name: str = "pft"
    """Dimension name for variables with an extra dimension of size `npft`."""
    cpft_dim_name: str = "cpft"
    """Dimension name for variables with an extra dimension of size `ncpft`."""
    nvg_dim_name: str = "nvg"
    """Dimension name for variables with an extra dimension of size `nnvg`."""
    type_dim_name: str = "type"
    """Dimension name for variables with an extra dimension of size `ntype`."""
    tile_dim_name: str = "tile"
    """Dimension name for variables with an extra dimension of size `nsurft`."""
    soil_dim_name: str = "soil"
    """Dimension name for variables with an extra dimension of size `JULES_SOIL::sm_levels`."""
    snow_dim_name: str = "snow"
    """Dimension name for variables with an extra dimension of size `JULES_SNOW::nsmax`."""
    sclayer_dim_name: str = "sclayer"
    """Dimension name for the layered soil biogeochemistry (`JULES_SOIL_BIOGEOCHEM::l_layeredc` = TRUE).

    Despite the similar name, unrelated to `JULES_SOIL_ECOSSE::dim_cslayer`.
    """
    scpool_dim_name: str = "scpool"
    """Dimension name for variables with an extra dimension of size `dim_cs1`, the soil carbon pools."""
    bedrock_dim_name: str = "bedrock"
    """Dimension name for variables with an extra dimension of size `JULES_SOIL::ns_deep`."""
    tracer_dim_name: str = "tracer"
    """Dimension name for variables with an extra dimension of size `JULES_DEPOSITION::ndry_dep_species`."""
    bl_level_dim_name: str = "bllevel"
    """Dimension name for variables with an extra dimension of size `JULES_NLSIZES::bl_levels`."""


class JulesLatlon(NamelistModel):
    """`JULES_LATLON` namelist members."""

    l_coord_latlon: bool = True
    """The coordinate system used for the model grid is latitude and longitude."""
    nvars: int = Field(default=0, ge=0)
    """The number of location variables that will be provided."""
    var: Annotated[list[str] | None, ListLen("nvars")] = None
    """List of location variable names as recognised by JULES."""
    use_file: Annotated[
        list[bool] | None, ListLen("nvars"), PerElementDefault(True, "nvars")
    ] = None
    """For each JULES variable, indicates if it should be read from file or use a constant value."""
    const_val: Annotated[list[float] | None, ListLen("nvars")] = None
    """For each JULES variable where use_file = FALSE, a constant value set at every point."""
    var_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """For each JULES variable where use_file = TRUE, this is the name of the variable in the file."""
    file: str | None = None
    """The file to read ancillary properties from."""
    tpl_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """For each JULES variable, the string to substitute into a templated file name."""
    read_from_dump: bool = False
    """Populate variables from the dump file if TRUE, otherwise use the other members."""

    @model_validator(mode="after")
    def _check_lists(self) -> "JulesLatlon":
        if self.nvars > 0:
            if self.var is None:
                raise ValueError("var is required when nvars > 0")
            for name in ("var", "use_file", "const_val", "var_name", "tpl_name"):
                val = getattr(self, name, None)
                if val is not None and len(val) != self.nvars:
                    raise ValueError(
                        f"{name} has {len(val)} element(s), expected nvars={self.nvars}"
                    )
        return self


class JulesLandFrac(NamelistModel):
    """`JULES_LAND_FRAC` namelist members."""

    file: str | None = None
    """The file to read land fraction data from."""
    land_frac_name: str | None = None
    """The name of the variable containing the land fraction data."""


class JulesModelGrid(NamelistModel):
    """`JULES_MODEL_GRID` namelist members."""

    force_1d_grid: bool = False
    """Force the model grid to be 1D, even if it would otherwise have been 2D."""
    l_land_area_only: bool = False
    land_only: bool = True
    """Model land points only, rather than all selected points."""
    use_subgrid: bool = False
    """The model grid is a subset of the full input grid, rather than all of it."""
    l_bounds: bool = False
    """Select the subgrid by coordinate bounds (TRUE) or by a list of points (FALSE).

    Only used when `use_subgrid` = TRUE. The coordinates are latitude and
    longitude when `JULES_LATLON::l_coord_latlon` = TRUE, and the projection
    coordinates otherwise.
    """
    x_bounds: Annotated[list[float], Field(min_length=2, max_length=2)] | None = None
    """Lower and upper bounds, in that order, for the x coordinate. Only used with `l_bounds` = TRUE."""
    y_bounds: Annotated[list[float], Field(min_length=2, max_length=2)] | None = None
    """Lower and upper bounds, in that order, for the y coordinate. Only used with `l_bounds` = TRUE."""
    npoints: int = Field(default=0, ge=0)
    """The number of points to model, read from `points_file`. Only used with `l_bounds` = FALSE."""
    points_file: str | None = None
    """File holding the coordinates of each point, one pair per line.

    Only used with `l_bounds` = FALSE.
    """

    @model_validator(mode="after")
    def _check_bounds_ordered(self) -> "JulesModelGrid":
        """Each pair of bounds must be given lower first."""
        for name in ("x_bounds", "y_bounds"):
            bounds = getattr(self, name)
            fail_if(
                bounds is not None and bounds[0] > bounds[1],
                f"{name}: the lower bound must not exceed the upper bound",
            )
        return self

    @model_validator(mode="after")
    def _warn_inactive_subgrid_members(self) -> "JulesModelGrid":
        """Warn about the subgrid members the selection method makes inactive."""
        if not self.use_subgrid:
            warn_inactive(self, ("l_bounds",), because="use_subgrid is false")
        elif self.l_bounds:
            warn_inactive(self, ("npoints", "points_file"), because="l_bounds is true")
        else:
            warn_inactive(self, ("x_bounds", "y_bounds"), because="l_bounds is false")
        return self


class JulesNlsizes(NamelistModel):
    """`JULES_NLSIZES` namelist members."""

    bl_levels: int = Field(default=1, ge=1)
    """Number of boundary layer levels.

    Only used when `JULES_DEPOSITION::l_deposition` = TRUE, where it sets the
    size of the input fields.
    """


class JulesSurfHgt(NamelistModel):
    """`JULES_SURF_HGT` namelist members.

    `l_elev_absolute_height` and `surf_hgt_io` are `nsurft`-length arrays, which
    is `npft + nnvg` unless `JULES_SURFACE::l_aggregate` = TRUE, when it is one.
    julesconf carries no `nsurft` dimension and so no `ListLen` here; see
    `UPSTREAM.md` §1.7.
    """

    l_tile_hgt: bool = False
    zero_height: bool = True
    """Set all surface tile elevations to zero. A very common configuration."""
    l_elev_absolute_height: list[bool] | None = None
    """Per surface tile, whether its elevation is absolute above sea level.

    FALSE means the elevation is relative to the gridbox mean. When any element
    is TRUE, the elevation of the forcing data must be supplied in
    `JULES_Z_LAND`.
    """
    use_file: bool = True
    """Read the surface tile elevations from `file` rather than from `surf_hgt_io`.

    Modelled as a scalar: the user guide types it `logical` with default `T` and
    every shipped configuration writes a scalar, while the rose metadata marks
    it an array without giving it a length rule. See `UPSTREAM.md` §1.6.
    """
    file: str | None = None
    """File holding the surface tile elevations relative to the gridbox mean."""
    surf_hgt_name: str = "surf_hgt"
    """Name in `file` of the variable holding the tile elevations.

    It must have a single levels dimension of size `nsurft`, named
    `JULES_INPUT_GRID::tile_dim_name`.
    """
    surf_hgt_io: list[float] | None = None
    """Surface tile elevations relative to the gridbox mean, for a single location.

    Only used with `use_file` = FALSE.
    """


class JulesZLand(NamelistModel):
    """`JULES_Z_LAND` namelist members.

    Optional; only used when some `JULES_SURF_HGT::l_elev_absolute_height` is
    TRUE. `surf_hgt_band` is `nsurft`-length — see `JulesSurfHgt` for why it
    carries no `ListLen`.
    """

    l_z_land: bool = False
    surf_hgt_band: list[float] | None = None
    """Spatially invariant elevation band for each surface tile.

    Absolute or relative to the gridbox mean according to
    `JULES_SURF_HGT::l_elev_absolute_height`.
    """
    use_file: bool = True
    """Read the forcing-data elevation from `file` rather than from `z_land_io`.

    Modelled as a scalar for the same reason as `JULES_SURF_HGT::use_file`; see
    `UPSTREAM.md` §1.6.
    """
    file: str | None = None
    """File holding the elevation of the forcing data."""
    z_land_name: str = "z_land"
    """Name in `file` of the variable holding the forcing-data elevation.

    It must have no level and no time dimensions.
    """
    z_land_io: float | None = None
    """Elevation of the forcing data for a single location.

    Only used with `use_file` = FALSE. Modelled as a scalar, following the user
    guide's `real` and the shipped configurations, against the rose metadata's
    unaccompanied array marking; see `UPSTREAM.md` §1.6.
    """


class ModelGridNamelist(NamelistModel):
    """Top-level schema for `model_grid.nml`."""

    jules_input_grid: JulesInputGrid = JulesInputGrid()
    jules_latlon: JulesLatlon = JulesLatlon()
    jules_land_frac: JulesLandFrac = JulesLandFrac()
    jules_model_grid: JulesModelGrid = JulesModelGrid()
    jules_nlsizes: JulesNlsizes = JulesNlsizes()
    jules_surf_hgt: JulesSurfHgt = JulesSurfHgt()
    jules_z_land: JulesZLand = JulesZLand()
