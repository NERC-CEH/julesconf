"""Validation schema for ``model_grid.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/model_grid.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["ModelGridNamelist"]


class JulesInputGrid(BaseModel):
    """``JULES_INPUT_GRID`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    grid_is_1d: bool = False
    nx: int = Field(default=1, ge=1)
    ny: int = Field(default=1, ge=1)
    dim_name: str = "land"
    x_dim_name: str = "x"
    y_dim_name: str = "y"
    time_dim_name: str = "time"
    land_frac_name: str = "land_frac"
    lat_name: str = "latitude"
    lon_name: str = "longitude"


class JulesLatlon(BaseModel):
    """``JULES_LATLON`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_coord_latlon: bool = True
    nvars: int = Field(default=0, ge=0)
    var: list[str] | None = None
    use_file: list[bool] | None = None
    const_val: list[float] | None = None
    var_name: list[str] | None = None
    file: str | None = None

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


class JulesLandFrac(BaseModel):
    """``JULES_LAND_FRAC`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class JulesModelGrid(BaseModel):
    """``JULES_MODEL_GRID`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    force_1d_grid: bool = False
    l_land_area_only: bool = False


class JulesNlsizes(BaseModel):
    """``JULES_NLSIZES`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class JulesSurfHgt(BaseModel):
    """``JULES_SURF_HGT`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_tile_hgt: bool = False


class JulesZLand(BaseModel):
    """``JULES_Z_LAND`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_z_land: bool = False


class ModelGridNamelist(BaseModel):
    """Top-level schema for ``model_grid.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_input_grid: JulesInputGrid = JulesInputGrid()
    jules_latlon: JulesLatlon = JulesLatlon()
    jules_land_frac: JulesLandFrac = JulesLandFrac()
    jules_model_grid: JulesModelGrid = JulesModelGrid()
    jules_nlsizes: JulesNlsizes = JulesNlsizes()
    jules_surf_hgt: JulesSurfHgt = JulesSurfHgt()
    jules_z_land: JulesZLand = JulesZLand()
