"""Validation schema for ``nveg_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/nveg_params.nml.rst``

All list fields have length ``nnvg`` (cross-namelist; validated in
:class:`~julesconf.schemas.namelists.JulesNamelists`).
"""

from typing import Annotated

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import ListLen, SentinelOrFraction, SentinelOrNonNegFloat

__all__ = ["NvegParamsNamelist"]


class JulesNvegparm(NamelistModel):
    """``JULES_NVEGPARM`` namelist members."""

    albsnc_nvg_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Snow-covered albedo."""
    albsnf_nvg_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Snow-free albedo."""
    albsnf_nvgu_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Upper limit on snow-free albedo when l_albedo_obs = TRUE."""
    albsnf_nvgl_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Lower limit on snow-free albedo when l_albedo_obs = TRUE."""
    catch_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Capacity for water (kg m⁻²)."""
    gs_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Surface conductance (m s⁻¹)."""
    infil_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Infiltration enhancement factor."""
    z0_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Roughness length for momentum (m)."""
    ch_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Heat capacity of this surface type (J K⁻¹ m⁻²)."""
    vf_nvg_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Fractional coverage of non-vegetation canopy."""
    emis_nvg_io: Annotated[list[SentinelOrFraction] | None, ListLen("nnvg")] = None
    """Surface emissivity of non-vegetated surfaces."""
    z0hm_nvg_io: Annotated[list[SentinelOrNonNegFloat] | None, ListLen("nnvg")] = None
    """Ratio of roughness length for heat to roughness length for momentum."""
    z0hm_classic_nvg_io: (
        Annotated[list[SentinelOrNonNegFloat], ListLen("nnvg")] | None
    ) = None
    """Ratio of roughness length for heat to momentum for the CLASSIC aerosol scheme only."""


class NvegParamsNamelist(NamelistModel):
    """Top-level schema for ``nveg_params.nml``."""

    jules_nvegparm: JulesNvegparm
