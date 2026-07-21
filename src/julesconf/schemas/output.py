"""Validation schema for `output.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/output.nml.rst`
"""

from typing import Literal

from pydantic import Field

from julesconf.schemas._base import NamelistModel

__all__ = ["OutputNamelist"]


class JulesOutput(NamelistModel):
    """`JULES_OUTPUT` namelist members."""

    output_dir: str | None = None
    """The directory used for output files."""
    run_id: str | None = None
    """A name or identifier for the run."""
    nprofiles: int = Field(default=0, ge=0)
    """The number of output profiles that will be specified."""
    dump_period: int = Field(default=1, ge=1)
    """The period between model dumps, unit depends on dump_period_unit."""
    dump_period_unit: Literal["Y", "T"] = "Y"
    """The unit/mode for the model dump period setting."""


class JulesOutputProfile(NamelistModel):
    """`JULES_OUTPUT_PROFILE` namelist members."""

    profile_name: str | None = None
    """The name of the output profile."""
    file_period: int = Field(default=0, ge=-3, le=0)
    """The period for output files, i.e. the time interval during which output goes to the same file."""
    output_spinup: bool = False
    """Determines whether the profile will provide output during model spin-up."""
    output_main_run: bool = False
    """Determines whether the profile will provide output during the main model run."""
    output_initial: bool = False
    """Determines whether the profile will output initial data for the sections."""
    output_start: str | None = None
    """The time to start collecting data for output."""
    output_end: str | None = None
    """The time to stop collecting data for output."""
    output_period: int | None = None
    """The period for output, in seconds."""
    l_land_frac: bool = False
    """Output gridbox land fraction to output profile."""

    nvars: int = Field(default=0, ge=0)
    """The number of variables that the profile will provide output for."""
    var: list[str] | None = None
    """List of variable names to output, as recognised by JULES."""
    output_type: list[str] | None = None
    """For each variable specified in var, this indicates the type of processing required."""


class OutputNamelist(NamelistModel):
    """Top-level schema for `output.nml`."""

    jules_output: JulesOutput = JulesOutput()
    jules_output_profile: JulesOutputProfile = JulesOutputProfile()
