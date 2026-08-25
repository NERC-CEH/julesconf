"""Validation schema for `timesteps.nml`.

Covers the `JULES_TIME` and `JULES_SPINUP` namelists.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/timesteps.nml.rst`
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import ListLen, PerElementDefault

__all__ = ["JulesSpinup", "JulesTime", "TimestepsNamelist"]

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


class JulesTime(NamelistModel):
    """`JULES_TIME` namelist members."""

    l_360: bool = False
    """Switch indicating use of 360 day years."""
    l_leap: bool = True
    """Switch indicating whether the calendar has leap years."""
    l_local_solar_time: bool = False
    """Switch indicating whether the time-stamping of the driving data is to be interpreted as local solar time."""
    timestep_len: int = Field(ge=1)
    """Model timestep length in seconds."""
    main_run_start: str
    """The start time for the integration."""
    main_run_end: str
    """The end time for the integration."""
    print_step: int = Field(default=1, ge=1)
    """Number of timesteps between printing timestep information to screen."""

    @field_validator("main_run_start", "main_run_end")
    @classmethod
    def _validate_datetime(cls, v: str) -> str:
        return _validate_jules_datetime(v)


class JulesSpinup(NamelistModel):
    """`JULES_SPINUP` namelist members."""

    max_spinup_cycles: int = Field(default=0, ge=0)
    """The maximum number of times the spin-up period is to be repeated."""
    spinup_start: str | None = None
    """The start time for each cycle of spin-up."""
    spinup_end: str | None = None
    """The end time for each cycle of spin-up."""
    terminate_on_spinup_fail: bool = False
    """Switch controlling behaviour if the model does not pass the spin-up test."""
    nvars: int = Field(default=0, ge=0)
    """The number of variables to use to assess if the model has spun up."""
    var: Annotated[list[_SpinupVar] | None, ListLen("nvars")] = None
    """List of variables to be used to determine if the model has spun up."""
    use_percent: Annotated[
        list[bool] | None, ListLen("nvars"), PerElementDefault(False, "nvars")
    ] = None
    """Indicates whether the tolerance for each variable is expressed as a percentage."""
    tolerance: Annotated[list[float] | None, ListLen("nvars")] = None
    """Tolerance for spin-up test for each variable."""

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


class TimestepsNamelist(NamelistModel):
    """Top-level schema for `timesteps.nml`.

    Usage:

        data = NamelistFileHandler().read("timesteps.nml")
        TimestepsNamelist.model_validate(data)
    """

    jules_time: JulesTime
    jules_spinup: JulesSpinup = Field(default_factory=JulesSpinup)
