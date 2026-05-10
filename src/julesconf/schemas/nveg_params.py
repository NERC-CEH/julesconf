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
    albsnf_nvg_io: list[float] | None = None
    albsnf_nvgu_io: list[float] | None = None
    albsnf_nvgl_io: list[float] | None = None
    catch_nvg_io: list[float] | None = None
    gs_nvg_io: list[float] | None = None
    infil_nvg_io: list[float] | None = None
    z0_nvg_io: list[float] | None = None
    ch_nvg_io: list[float] | None = None
    vf_nvg_io: list[float] | None = None
    emis_nvg_io: list[float] | None = None
    z0hm_nvg_io: list[float] | None = None
    z0hm_classic_nvg_io: list[float] | None = None


class NvegParamsNamelist(BaseModel):
    """Top-level schema for ``nveg_params.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_nvegparm: JulesNvegparm
