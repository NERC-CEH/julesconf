"""Validation schema for `jules_surface_types.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface_types.nml.rst`
"""

from typing import ClassVar

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if

__all__ = ["JulesSurfaceTypes", "JulesSurfaceTypesNamelist"]


class JulesSurfaceTypes(NamelistModel):
    """`JULES_SURFACE_TYPES` namelist members."""

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

    _PFT_MEMBERS: ClassVar[tuple[str, ...]] = (
        "brd_leaf",
        "brd_leaf_dec",
        "brd_leaf_eg_trop",
        "brd_leaf_eg_temp",
        "ndl_leaf",
        "ndl_leaf_dec",
        "ndl_leaf_eg",
        "c3_grass",
        "c3_crop",
        "c3_pasture",
        "c4_grass",
        "c4_crop",
        "c4_pasture",
        "shrub",
        "shrub_dec",
        "shrub_eg",
    )
    """Members naming a vegetated surface type, which must index a PFT."""

    _NVG_MEMBERS: ClassVar[tuple[str, ...]] = (
        "urban",
        "lake",
        "soil",
        "ice",
        "urban_canyon",
        "urban_roof",
        "elev_ice",
        "elev_rock",
    )
    """Members naming a non-vegetated surface type, which must index past the PFTs."""

    @model_validator(mode="after")
    def _check_ncpft(self) -> "JulesSurfaceTypes":
        if self.ncpft >= self.npft:
            raise ValueError(f"ncpft={self.ncpft} must be < npft={self.npft}")
        return self

    @model_validator(mode="after")
    def _check_pseudo_levels(self) -> "JulesSurfaceTypes":
        """Check every surface type index against `npft` and `nnvg`.

        JULES lays the surface types out as the `npft` PFTs followed by the
        `nnvg` non-vegetated types, so a vegetated index must be at most
        `npft`, and a non-vegetated one must be greater than `npft` and at
        most `npft + nnvg`. `-1` is the "not used" sentinel for the elevated
        types.
        """
        ntype = self.npft + self.nnvg
        for member in self._PFT_MEMBERS:
            value = getattr(self, member)
            fail_if(
                value is not None and value > self.npft,
                f"{member}: Pseudo level must be less than or equal to npft",
            )
        for member in (*self._NVG_MEMBERS, "usr_type"):
            value = getattr(self, member)
            if value is None or value == -1:
                continue
            fail_if(
                value > ntype,
                f"{member}: Pseudo level must be less than or equal to npft+nnvg",
            )
            # The metadata gives `usr_type` the upper bound only: a user type
            # may legitimately be numbered among the PFTs.
            fail_if(
                member != "usr_type" and value <= self.npft,
                f"{member}: PFTs must be grouped together first with"
                " non-vegetated tiles following",
            )
        return self

    @model_validator(mode="after")
    def _check_urban_tiles(self) -> "JulesSurfaceTypes":
        """The one-tile and two-tile urban schemes are mutually exclusive."""
        one_tile = (self.urban or 0) > 0
        canyon = (self.urban_canyon or 0) > 0
        roof = (self.urban_roof or 0) > 0
        fail_if(
            one_tile and (canyon or roof),
            "urban cannot be combined with urban_canyon/urban_roof:"
            " use either the one-tile or the two-tile urban scheme",
        )
        fail_if(
            canyon != roof,
            "Both the canyon and roof surface type must be present",
        )
        return self


class JulesSurfaceTypesNamelist(NamelistModel):
    """Top-level schema for `jules_surface_types.nml`."""

    jules_surface_types: JulesSurfaceTypes
