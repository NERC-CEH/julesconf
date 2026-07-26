"""Validation schema for `prescribed_data.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/prescribed_data.nml.rst`
"""

from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.constraints import ListLen, PerElementDefault

__all__ = [
    "JulesPrescribed",
    "JulesPrescribedDataset",
    "PrescribedDataNamelist",
]


class JulesPrescribed(NamelistModel):
    """`JULES_PRESCRIBED` namelist members."""

    n_datasets: int = Field(default=0, ge=0)
    """The number of datasets specified using instances of JULES_PRESCRIBED_DATASET."""


class JulesPrescribedDataset(NamelistModel):
    """`JULES_PRESCRIBED_DATASET` namelist members.

    JULES reads this namelist `JULES_PRESCRIBED::n_datasets` times, once per
    dataset. julesconf models a single instance; see
    `julesconf.schemas.RepeatedNamelistGroupWarning`.
    """

    data_start: str | None = None
    """Start time of the first timestep of data."""
    data_end: str | None = None
    """End time of the last timestep of data."""
    data_period: int | None = None
    """Period of the data in seconds; `-1` for monthly and `-2` for annual."""
    is_climatology: bool = False
    """Use the data as a climatology. Exactly one year of data must be given."""
    read_list: bool = False
    """Read a list of file names with start times, rather than a single file."""
    nfiles: int = Field(default=0, ge=0)
    """Number of files to read names and start times for. Used if `read_list`."""
    file: str | None = None
    """The data file, file name template, or -- if `read_list` -- the list file."""
    nvars: int = Field(default=0, ge=0)
    """The number of variables the dataset provides."""
    var: Annotated[list[str] | None, ListLen("nvars")] = None
    """List of variable names as recognised by JULES."""
    var_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """For each variable in `var`, the name of the variable in the file."""
    tpl_name: Annotated[
        list[str] | None, ListLen("nvars"), PerElementDefault("", "nvars")
    ] = None
    """For each variable in `var`, the string to substitute into a templated name."""
    interp: Annotated[list[str] | None, ListLen("nvars")] = None
    """For each variable in `var`, the method of time interpolation."""
    prescribed_levels: list[int] | None = None
    """Indices of the levels to prescribe. Only implemented for `sthuf`."""

    @model_validator(mode="after")
    def _check_lists(self) -> "JulesPrescribedDataset":
        """Check the per-variable lists against `nvars`."""
        for name in ("var", "var_name", "tpl_name", "interp"):
            value = getattr(self, name)
            if value is not None and len(value) != self.nvars:
                raise ValueError(
                    f"{name} has {len(value)} element(s), expected nvars={self.nvars}"
                )
        if self.nvars > 0 and self.var is None:
            raise ValueError("var is required when nvars > 0")
        return self


class PrescribedDataNamelist(NamelistModel):
    """Top-level schema for `prescribed_data.nml`."""

    jules_prescribed: JulesPrescribed = JulesPrescribed()
    jules_prescribed_dataset: JulesPrescribedDataset = JulesPrescribedDataset()
