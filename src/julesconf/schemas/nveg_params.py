"""Validation schema for ``nveg_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/nveg_params.nml.rst``

All list fields have length ``nnvg`` (cross-namelist; validated in
:class:`~julesconf.schemas.namelists.JulesNamelists`).
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["NvegParamsNamelist"]


class JulesNvegparm(BaseModel):
    """``JULES_NVEGPARM`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    albsnc_nvg_io: list[float] | None = None
    """Snow-covered albedo."""
    albsnf_nvg_io: list[float] | None = None
    """Snow-free albedo."""
    albsnf_nvgu_io: list[float] | None = None
    """Upper limit on snow-free albedo when l_albedo_obs = TRUE."""
    albsnf_nvgl_io: list[float] | None = None
    """Lower limit on snow-free albedo when l_albedo_obs = TRUE."""
    catch_nvg_io: list[float] | None = None
    """Capacity for water (kg m⁻²)."""
    gs_nvg_io: list[float] | None = None
    """Surface conductance (m s⁻¹)."""
    infil_nvg_io: list[float] | None = None
    """Infiltration enhancement factor."""
    z0_nvg_io: list[float] | None = None
    """Roughness length for momentum (m)."""
    ch_nvg_io: list[float] | None = None
    """Heat capacity of this surface type (J K⁻¹ m⁻²)."""
    vf_nvg_io: list[float] | None = None
    """Fractional coverage of non-vegetation canopy."""
    emis_nvg_io: list[float] | None = None
    """Surface emissivity of non-vegetated surfaces."""
    z0hm_nvg_io: list[float] | None = None
    """Ratio of roughness length for heat to roughness length for momentum."""
    z0hm_classic_nvg_io: list[float] | None = None
    """Ratio of roughness length for heat to momentum for the CLASSIC aerosol scheme only."""


class NvegParamsNamelist(BaseModel):
    """Top-level schema for ``nveg_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_nvegparm: JulesNvegparm
