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
    """The number of plant functional types (PFTs) to be modelled."""
    nnvg: int = Field(ge=1)
    """The number of non-plant surface types to be modelled."""
    ncpft: int = Field(default=0, ge=0)
    """The number of crop plant functional types to be modelled."""

    # Non-vegetated surface type indices
    urban: int | None = None
    """Index of the urban surface type (#6)."""
    lake: int | None = None
    """Index of the lake surface type (#7)."""
    soil: int | None = None
    """Index of the soil surface type (#8)."""
    ice: int | None = None
    """Index of the ice surface type (#9)."""
    urban_canyon: int | None = None
    """Index of the urban canyon surface type (#601)."""
    urban_roof: int | None = None
    """Index of the urban roof surface type (#602)."""
    elev_ice: int | None = None
    """Indices of the elevated ice types (#901-925)."""
    elev_rock: int | None = None
    """Indices of the elevated non-glaciated bedrock types (#926-950)."""
    usr_type: int | None = None
    """Index of user specified surface type (#10-99)."""

    # Vegetated surface type indices
    brd_leaf: int | None = None
    """Index of the original broadleaf PFT surface type (#1)."""
    brd_leaf_dec: int | None = None
    """Index of broadleaf (deciduous) PFT surface type (#101)."""
    brd_leaf_eg_trop: int | None = None
    """Index of broadleaf (evergreen tropical) PFT surface type (#102)."""
    brd_leaf_eg_temp: int | None = None
    """Index of broadleaf (evergreen temperate) PFT surface type (#103)."""
    ndl_leaf: int | None = None
    """Index of original needleleaf PFT surface type (#2)."""
    ndl_leaf_dec: int | None = None
    """Index of needleleaf (deciduous) PFT surface type (#201)."""
    ndl_leaf_eg: int | None = None
    """Index of needleleaf (evergreen) PFT surface type (#202)."""
    c3_grass: int | None = None
    """Index of original C3 grass PFT surface type (#3)."""
    c3_crop: int | None = None
    """Index of C3 crop PFT surface type (#301)."""
    c3_pasture: int | None = None
    """Index of C3 pasture PFT surface type (#302)."""
    c4_grass: int | None = None
    """Index of original C4 grass PFT surface type (#4)."""
    c4_crop: int | None = None
    """Index of C4 crop PFT surface type (#401)."""
    c4_pasture: int | None = None
    """Index of C4 pasture PFT surface type (#402)."""
    shrub: int | None = None
    """Index of original shrub PFT surface type (#5)."""
    shrub_dec: int | None = None
    """Index of shrub (deciduous) PFT surface type (#501)."""
    shrub_eg: int | None = None
    """Index of shrub (evergreen) PFT surface type (#502)."""

    @model_validator(mode="after")
    def _check_ncpft(self) -> "JulesSurfaceTypes":
        if self.ncpft >= self.npft:
            raise ValueError(f"ncpft={self.ncpft} must be < npft={self.npft}")
        return self


class JulesSurfaceTypesNamelist(BaseModel):
    """Top-level schema for ``jules_surface_types.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_surface_types: JulesSurfaceTypes
