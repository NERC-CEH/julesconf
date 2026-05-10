"""Validation schema for ``jules_surface_types.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface_types.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["JulesSurfaceTypesNamelist"]


class JulesSurfaceTypes(BaseModel):
    """``JULES_SURFACE_TYPES`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    npft: int = Field(ge=1)
    nnvg: int = Field(ge=1)
    ncpft: int = Field(default=0, ge=0)

    # Non-vegetated surface type indices
    urban: int | None = None
    lake: int | None = None
    soil: int | None = None
    ice: int | None = None
    urban_canyon: int | None = None
    urban_roof: int | None = None
    elev_ice: int | None = None
    elev_rock: int | None = None
    usr_type: int | None = None

    # Vegetated surface type indices
    brd_leaf: int | None = None
    brd_leaf_dec: int | None = None
    brd_leaf_eg_trop: int | None = None
    brd_leaf_eg_temp: int | None = None
    ndl_leaf: int | None = None
    ndl_leaf_dec: int | None = None
    ndl_leaf_eg: int | None = None
    c3_grass: int | None = None
    c3_crop: int | None = None
    c3_pasture: int | None = None
    c4_grass: int | None = None
    c4_crop: int | None = None
    c4_pasture: int | None = None
    shrub: int | None = None
    shrub_dec: int | None = None
    shrub_eg: int | None = None

    @model_validator(mode="after")
    def _check_ncpft(self) -> "JulesSurfaceTypes":
        if self.ncpft >= self.npft:
            raise ValueError(f"ncpft={self.ncpft} must be < npft={self.npft}")
        return self


class JulesSurfaceTypesNamelist(BaseModel):
    """Top-level schema for ``jules_surface_types.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_surface_types: JulesSurfaceTypes
