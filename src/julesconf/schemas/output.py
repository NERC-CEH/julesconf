"""Validation schema for ``output.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/output.nml.rst``
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["OutputNamelist"]


class JulesOutput(BaseModel):
    """``JULES_OUTPUT`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    output_dir: str | None = None
    run_id: str | None = None
    nprofiles: int = Field(default=0, ge=0)
    dump_period: int = Field(default=1, ge=1)
    dump_period_unit: Literal["Y", "T"] = "Y"


class JulesOutputProfile(BaseModel):
    """``JULES_OUTPUT_PROFILE`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    profile_name: str | None = None
    file_period: int = Field(default=0, ge=-3, le=0)
    output_spinup: bool = False
    output_main_run: bool = False
    output_initial: bool = False
    output_start: str | None = None
    output_end: str | None = None
    output_period: int | None = None
    l_land_frac: bool = False

    nvars: int = Field(default=0, ge=0)
    var: list[str] | None = None
    output_type: list[str] | None = None


class OutputNamelist(BaseModel):
    """Top-level schema for ``output.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_output: JulesOutput = JulesOutput()
    jules_output_profile: JulesOutputProfile = JulesOutputProfile()
