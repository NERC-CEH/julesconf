"""Validation schema for ``timesteps.nml``.

Covers the ``JULES_TIME`` and ``JULES_SPINUP`` namelists.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/timesteps.nml.rst``
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = ["TimestepsNamelist"]

_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_SpinupVar = Literal["c_soil", "c_veg", "smcl", "t_soil"]


def _validate_jules_datetime(v: str) -> str:
    try:
        datetime.strptime(v, _DATETIME_FORMAT)
    except ValueError as err:
        raise ValueError(
            f"Expected datetime format 'yyyy-mm-dd hh:mm:ss', got '{v}'"
        ) from err
    return v


class JulesTime(BaseModel):
    """``JULES_TIME`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_360: bool = False
    l_leap: bool = True
    l_local_solar_time: bool = False
    timestep_len: int = Field(ge=1)
    main_run_start: str
    main_run_end: str
    print_step: int = Field(default=1, ge=1)

    @field_validator("main_run_start", "main_run_end")
    @classmethod
    def _validate_datetime(cls, v: str) -> str:
        return _validate_jules_datetime(v)


class JulesSpinup(BaseModel):
    """``JULES_SPINUP`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    max_spinup_cycles: int = Field(default=0, ge=0)
    spinup_start: str | None = None
    spinup_end: str | None = None
    terminate_on_spinup_fail: bool = False
    nvars: int = Field(default=0, ge=0)
    var: list[_SpinupVar] | None = None
    use_percent: list[bool] | None = None
    tolerance: list[float] | None = None

    @field_validator("spinup_start", "spinup_end")
    @classmethod
    def _validate_datetime(cls, v: str | None) -> str | None:
        return None if v is None else _validate_jules_datetime(v)

    @model_validator(mode="after")
    def _check_spinup_consistency(self) -> "JulesSpinup":
        if self.max_spinup_cycles > 0:
            if self.spinup_start is None:
                raise ValueError("spinup_start is required when max_spinup_cycles > 0")
            if self.spinup_end is None:
                raise ValueError("spinup_end is required when max_spinup_cycles > 0")

        if self.nvars > 0:
            if self.var is None:
                raise ValueError("var is required when nvars > 0")
            if len(self.var) != self.nvars:
                raise ValueError(
                    f"var has {len(self.var)} element(s), expected nvars={self.nvars}"
                )
            if self.tolerance is None:
                raise ValueError("tolerance is required when nvars > 0")
            if len(self.tolerance) != self.nvars:
                raise ValueError(
                    f"tolerance has {len(self.tolerance)} element(s),"
                    f" expected nvars={self.nvars}"
                )
            if self.use_percent is not None and len(self.use_percent) != self.nvars:
                raise ValueError(
                    f"use_percent has {len(self.use_percent)} element(s),"
                    f" expected nvars={self.nvars}"
                )

        return self


class TimestepsNamelist(BaseModel):
    """Top-level schema for ``timesteps.nml``.

    Usage::

        data = NamelistFileHandler().read("timesteps.nml")
        TimestepsNamelist.model_validate(data)
    """

    model_config = ConfigDict(extra="ignore")

    jules_time: JulesTime
    jules_spinup: JulesSpinup = Field(default_factory=JulesSpinup)
