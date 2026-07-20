"""Validation schema for ``drive.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/drive.nml.rst``
"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from julesconf.schemas._base import NamelistModel

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


class JulesDrive(NamelistModel):
    """``JULES_DRIVE`` namelist members."""

    file: str | None = None
    """File containing data or template for data file names."""
    data_start: str | None = None
    """Time of start of first timestep of data."""
    data_end: str | None = None
    """Time of end of last timestep of data."""
    data_period: int | None = None  # -2, -1 or > 0
    """Period in seconds of the data."""
    read_list: bool = False
    """Switch controlling how data file names are determined."""
    nfiles: int = Field(default=0, ge=0)
    """Number of data files to read names and times for."""

    nvars: int = Field(default=0, ge=0)
    """Number of forcing variables that will be provided."""
    var: list[str] | None = None
    """List of forcing variable names as recognised by JULES."""
    var_name: list[str] | None = None
    """Name of variable in file for each JULES variable specified."""
    tpl_name: list[str] | None = None
    """String to substitute into file names for variable name templating."""
    interp: list[str] | None = None
    """How each variable is to be interpolated in time."""

    # Meteorological parameters
    t_for_snow: float | None = None
    """Temperature threshold below which precipitation is treated as snowfall."""
    t_for_con_rain: float | None = None
    """Temperature threshold above which rainfall is treated as convective."""
    diff_frac_const: float | None = None
    """Constant value to calculate diffuse radiation from total shortwave."""
    z1_uv_in: float | None = Field(default=None, gt=0)
    """Constant height value where wind data are valid for every point."""
    z1_tq_in: float | None = Field(default=None, gt=0)
    """Constant height value for temperature and humidity data."""
    z1_tq_vary: bool = False
    """Switch for spatially varying temperature/humidity data height."""
    z1_tq_file: str | None = None
    """File to read spatially varying temperature/humidity height from."""
    z1_tq_var_name: str = "z1_tq_in"
    """Variable name in file containing temperature/humidity height data."""
    bl_height: float = Field(default=1000.0, gt=0)
    """Height above ground to top of atmospheric boundary layer."""

    # Daily disaggregator
    l_daily_disagg: bool = False
    """Switch controlling whether disaggregator converts daily to model timestep."""
    l_disagg_const_rh: bool = False
    """Switch controlling sub-daily disaggregation of humidity."""
    dur_conv_rain: float | None = None
    """Duration of convective rainfall event in seconds for disaggregator."""
    dur_ls_rain: float | None = None
    """Duration of large-scale rainfall event in seconds for disaggregator."""
    dur_conv_snow: float | None = None
    """Duration of convective snowfall event in seconds for disaggregator."""
    dur_ls_snow: float | None = None
    """Duration of large-scale snowfall event in seconds for disaggregator."""
    precip_disagg_method: int | None = Field(default=None, ge=1, le=4)
    """Switch controlling the disaggregation method for precipitation."""

    # Perturbations
    l_perturb_driving: bool = False
    """Apply perturbation to driving data."""
    temperature_abs_perturbation: float | None = None
    """Absolute perturbation amount to add to temperature."""
    precip_rel_perturbation: float | None = Field(default=None, ge=0)
    """Relative perturbation for precipitation variables."""

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


class DriveNamelist(NamelistModel):
    """Top-level schema for ``drive.nml``."""

    jules_drive: JulesDrive
