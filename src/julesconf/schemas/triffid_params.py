"""Validation schema for ``triffid_params.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/triffid_params.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["TriffidParamsNamelist"]


class JulesTriffid(BaseModel):
    """``JULES_TRIFFID`` namelist members.

    Contains npft-length lists of TRIFFID dynamic vegetation parameters.
    Only used when :nml:mem:`JULES_VEGETATION::l_triffid` = TRUE.
    """

    model_config = ConfigDict(extra="ignore")

    crop_io: list[int] | None = None
    g_area_io: list[float] | None = None
    g_grow_io: list[float] | None = None
    g_root_io: list[float] | None = None
    g_wood_io: list[float] | None = None
    lai_max_io: list[float] | None = None
    lai_min_io: list[float] | None = None
    alloc_fast_io: list[float] | None = None
    alloc_med_io: list[float] | None = None
    alloc_slow_io: list[float] | None = None
    dpm_rpm_ratio_io: list[float] | None = None
    retrans_n_io: list[float] | None = None
    retrans_p_io: list[float] | None = None
    ag_sales_io: list[float] | None = None
    ag_plant_io: list[float] | None = None


class TriffidParamsNamelist(BaseModel):
    """Top-level schema for ``triffid_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_triffid: JulesTriffid = JulesTriffid()
