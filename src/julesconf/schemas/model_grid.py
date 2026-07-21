"""Validation schema for `model_grid.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/model_grid.nml.rst`
"""

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel

__all__ = ["ModelGridNamelist"]


class JulesInputGrid(NamelistModel):
    """`JULES_INPUT_GRID` namelist members."""

    grid_is_1d: bool = False
    """Indicates if the input grid is 1D or 2D."""
    nx: int = Field(default=1, ge=1)
    """The size of the x dimension."""
    ny: int = Field(default=1, ge=1)
    """The size of the y dimension."""
    dim_name: str = "land"
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


class JulesLatlon(NamelistModel):
    """`JULES_LATLON` namelist members."""

    l_coord_latlon: bool = True
    """The coordinate system used for the model grid is latitude and longitude."""
    nvars: int = Field(default=0, ge=0)
    """The number of location variables that will be provided."""
    var: list[str] | None = None
    """List of location variable names as recognised by JULES."""
    use_file: list[bool] | None = None
    """For each JULES variable, indicates if it should be read from file or use a constant value."""
    const_val: list[float] | None = None
    """For each JULES variable where use_file = FALSE, a constant value set at every point."""
    var_name: list[str] | None = None
    """For each JULES variable where use_file = TRUE, this is the name of the variable in the file."""
    file: str | None = None
    """The file to read ancillary properties from."""

    @model_validator(mode="after")
    def _check_lists(self) -> "JulesLatlon":
        if self.nvars > 0:
            if self.var is None:
                raise ValueError("var is required when nvars > 0")
            for name in ("var", "use_file", "const_val", "var_name"):
                val = getattr(self, name, None)
                if val is not None and len(val) != self.nvars:
                    raise ValueError(
                        f"{name} has {len(val)} element(s), expected nvars={self.nvars}"
                    )
        return self


class JulesLandFrac(NamelistModel):
    """`JULES_LAND_FRAC` namelist members."""


class JulesModelGrid(NamelistModel):
    """`JULES_MODEL_GRID` namelist members."""

    force_1d_grid: bool = False
    """Force the model grid to be 1D, even if it would otherwise have been 2D."""
    l_land_area_only: bool = False


class JulesNlsizes(NamelistModel):
    """`JULES_NLSIZES` namelist members."""


class JulesSurfHgt(NamelistModel):
    """`JULES_SURF_HGT` namelist members."""

    l_tile_hgt: bool = False


class JulesZLand(NamelistModel):
    """`JULES_Z_LAND` namelist members."""

    l_z_land: bool = False


class ModelGridNamelist(NamelistModel):
    """Top-level schema for `model_grid.nml`."""

    jules_input_grid: JulesInputGrid = JulesInputGrid()
    jules_latlon: JulesLatlon = JulesLatlon()
    jules_land_frac: JulesLandFrac = JulesLandFrac()
    jules_model_grid: JulesModelGrid = JulesModelGrid()
    jules_nlsizes: JulesNlsizes = JulesNlsizes()
    jules_surf_hgt: JulesSurfHgt = JulesSurfHgt()
    jules_z_land: JulesZLand = JulesZLand()
