"""Validation schema for `jules_surface_types.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_surface_types.nml.rst`
"""

from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._conditional import fail_if
from julesconf.schemas.constraints import ListLen

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
    elev_ice: list[int] | None = None
    """Indices of the elevated ice types (#901-925).

    An array: the elevated-tile (glacier/ice sheet) scheme divides the ice
    surface into any number of elevation bands, each of which is its own
    surface type. `-1` is the "not in use" sentinel.
    """
    elev_rock: list[int] | None = None
    """Indices of the elevated non-glaciated bedrock types (#926-950).

    An array, for the same reason as `elev_ice`.
    """
    usr_type: list[int] | None = None
    """Indices of the user specified surface types (#10-99).

    Unlike every other surface type identifier this is an array: a
    configuration may define any number of user types, each of which may be
    either vegetated or non-vegetated, so the permitted range is the whole
    of `1:ntype`.
    """

    tile_map_ids: Annotated[
        list[Annotated[int, Field(ge=1)]] | None, ListLen("ntype")
    ] = None
    """Mapping from the input dump's surface type configuration to this one.

    One entry per surface type. Not available to JULES standalone; documented
    only in the rose metadata.
    """

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
    )
    """Members naming a non-vegetated surface type, which must index past the PFTs."""

    _NVG_ARRAY_MEMBERS: ClassVar[tuple[str, ...]] = ("elev_ice", "elev_rock")
    """Non-vegetated members holding an *array* of surface type indices.

    The elevated ice and bedrock schemes each define one surface type per
    elevation band, so these carry the same constraints as `_NVG_MEMBERS` but
    element by element.
    """

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

        `usr_type`, `elev_ice` and `elev_rock` are arrays and are checked
        element by element. A user type may be either vegetated or
        non-vegetated, so the user guide gives `usr_type` the whole of
        `1:ntype` and the metadata rule is `any(this > npft + nnvg)` — an
        upper bound only, over a list. `elev_ice` and `elev_rock` carry both
        the metadata's `any(...)` rules, so each element must lie past the
        PFTs unless it is the `-1` sentinel.
        """
        ntype = self.npft + self.nnvg
        for member in self._PFT_MEMBERS:
            value = getattr(self, member)
            fail_if(
                value is not None and value > self.npft,
                f"{member}: Pseudo level must be less than or equal to npft",
            )
        for member in self._NVG_MEMBERS:
            value = getattr(self, member)
            if value is None or value == -1:
                continue
            fail_if(
                value > ntype,
                f"{member}: Pseudo level must be less than or equal to npft+nnvg",
            )
            fail_if(
                value <= self.npft,
                f"{member}: PFTs must be grouped together first with"
                " non-vegetated tiles following",
            )
        for member in self._NVG_ARRAY_MEMBERS:
            for index, value in enumerate(getattr(self, member) or ()):
                if value == -1:
                    continue
                fail_if(
                    value > ntype,
                    f"{member}[{index}]: Pseudo level must be less than or"
                    " equal to npft+nnvg",
                )
                fail_if(
                    value <= self.npft,
                    f"{member}[{index}]: PFTs must be grouped together first"
                    " with non-vegetated tiles following",
                )
        for index, value in enumerate(self.usr_type or ()):
            fail_if(
                value > ntype,
                f"usr_type[{index}]: Pseudo level must be less than or equal"
                " to npft+nnvg",
            )
            fail_if(
                value < 1,
                f"usr_type[{index}]: Pseudo level must be greater than or equal to 1",
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
