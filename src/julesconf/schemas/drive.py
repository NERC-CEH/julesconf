"""Validation schema for ``drive.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/drive.nml.rst``
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = ["DriveNamelist"]

_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _validate_datetime(v: str) -> str:
    try:
        datetime.strptime(v, _DATETIME_FORMAT)
    except ValueError as err:
        raise ValueError(
            f"Expected datetime format 'yyyy-mm-dd hh:mm:ss', got '{v}'"
        ) from err
    return v


class JulesDrive(BaseModel):
    """``JULES_DRIVE`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    file: str | None = None
    data_start: str | None = None
    data_end: str | None = None
    data_period: int | None = None  # -2, -1 or > 0
    read_list: bool = False
    nfiles: int = Field(default=0, ge=0)

    nvars: int = Field(default=0, ge=0)
    var: list[str] | None = None
    var_name: list[str] | None = None
    tpl_name: list[str] | None = None
    interp: list[str] | None = None

    # Meteorological parameters
    t_for_snow: float | None = None
    t_for_con_rain: float | None = None
    diff_frac_const: float | None = None
    z1_uv_in: float | None = Field(default=None, gt=0)
    z1_tq_in: float | None = Field(default=None, gt=0)
    z1_tq_vary: bool = False
    z1_tq_file: str | None = None
    z1_tq_var_name: str = "z1_tq_in"
    bl_height: float = Field(default=1000.0, gt=0)

    # Daily disaggregator
    l_daily_disagg: bool = False
    l_disagg_const_rh: bool = False
    dur_conv_rain: float | None = None
    dur_ls_rain: float | None = None
    dur_conv_snow: float | None = None
    dur_ls_snow: float | None = None
    precip_disagg_method: int | None = Field(default=None, ge=1, le=4)

    # Perturbations
    l_perturb_driving: bool = False
    temperature_abs_perturbation: float | None = None
    precip_rel_perturbation: float | None = Field(default=None, ge=0)

    @field_validator("data_start", "data_end")
    @classmethod
    def _validate_datetime_field(cls, v: str | None) -> str | None:
        return None if v is None else _validate_datetime(v)

    @model_validator(mode="after")
    def _check_data_period(self) -> "JulesDrive":
        if (
            self.data_period is not None
            and self.data_period not in (-2, -1)
            and self.data_period <= 0
        ):
            raise ValueError(
                f"data_period must be -2, -1 or > 0, got {self.data_period}"
            )
        return self

    @model_validator(mode="after")
    def _check_var_lists(self) -> "JulesDrive":
        if self.nvars > 0:
            if self.var is None:
                raise ValueError("var is required when nvars > 0")
            if len(self.var) != self.nvars:
                raise ValueError(
                    f"var has {len(self.var)} element(s), expected nvars={self.nvars}"
                )
            if self.interp is not None and len(self.interp) != self.nvars:
                raise ValueError(
                    f"interp has {len(self.interp)} element(s),"
                    f" expected nvars={self.nvars}"
                )
        return self


class DriveNamelist(BaseModel):
    """Top-level schema for ``drive.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_drive: JulesDrive
