"""Configuration module for the JULES land surface model.

Provides DirConfig-based handlers and configurations for reading and writing
JULES configuration files, including Fortran namelists, ASCII data files,
and NetCDF datasets.

The JULES (Joint UK Land Environment Simulator) model uses a directory-based
configuration layout with roughly 30 namelist files organized by physical process
and model component, plus input data files for initial conditions, tile fractions,
and driving (meteorological forcing) data.

This module defines:

- `NamelistFileHandler`: reads/writes Fortran namelist files via `f90nml`.
- `NamelistConfig`: a `DirConfig` subclass representing a complete namelists
  directory with all required `.nml` files.
- `AsciiFileHandler`: reads/writes plain-text ASCII data files via `numpy`.
- `NetcdfFileHandler`: reads/writes NetCDF datasets via `xarray`.
- `InputFilesConfig`: a `DirConfig` subclass for the input data directory.
- `JulesConfig`: the top-level `DirConfig` combining namelists and inputs.

Example usage:

    config = JulesConfig(
        namelists="namelists",
        inputs={
            "path": "inputs",
            "handler": lambda: InputFilesConfig(
                initial_conditions="initial_conditions.dat",
                tile_fractions="tile_fractions.dat",
                driving_data="driving_data.nc",
            ),
        },
    )
    config_dict = config.read("/path/to/jules/config")
    config.write("/path/to/output", config_dict)
"""

import dataclasses
import json
from os import PathLike
from pathlib import Path
from typing import Any, TypedDict

import dirconf
import f90nml
import numpy
import xarray
from dirconf import Node
from dirconf.config import DirConfig
from dirconf.node import path_to_node, to_node

__all__ = [
    "AsciiFileHandler",
    "InputFilesConfig",
    "JulesConfig",
    "NamelistConfig",
    "NamelistFileHandler",
    "NetcdfFileHandler",
    "namelist_to_dict",
]


def namelist_to_dict(data: f90nml.Namelist) -> dict:
    """Normalise a parsed `f90nml` namelist into julesconf's dict form.

    This is the boundary at which the one-vs-many ambiguity of a repeated
    Fortran group is resolved. `f90nml` returns a bare `Namelist` for a group
    that occurs once, a `Cogroup` for one that occurs more than once, and
    `_grp_<group>_<n>` keys once `Namelist.todict()` flattens either. Every
    group in `julesconf.schemas.REPEATABLE_GROUPS` is returned here as a
    `list[dict]` instead, of length one when the file had one occurrence, so
    nothing downstream has to know how `f90nml` chose to represent it.

    Args:
        data: A namelist as returned by `f90nml.read` or `f90nml.reads`.

    Returns:
        A `{block: {member: value}}` dict of plain JSON types, in which a
        repeatable group maps to a list of block dicts, one per occurrence.
    """
    from julesconf.schemas import REPEATABLE_GROUPS

    plain: dict[str, Any] = {}
    # `Namelist.items()` yields a repeated group once per occurrence, and its
    # keys are `NmlKey`s that index straight back to that one occurrence.
    # Plain `str` keys are what return the whole `Cogroup`, so de-duplicate
    # into those, in first-seen order.
    for group in dict.fromkeys(str(key) for key in data):
        value = data[group]
        # A Cogroup is a list subclass, so this catches both the two-or-more
        # case and the single-occurrence one.
        blocks = list(value) if isinstance(value, list) else [value]
        if group in REPEATABLE_GROUPS:
            plain[group] = [dict(block) for block in blocks]
        elif len(blocks) == 1:
            plain[group] = dict(blocks[0])
        else:
            # A group julesconf models as a single block, repeated anyway.
            # Keep `f90nml`'s `_grp_` naming rather than quietly picking one:
            # the schemas recognise it and raise `RepeatedNamelistGroupWarning`,
            # which is the whole point of not choosing here.
            for index, block in enumerate(blocks):
                plain[f"_grp_{group}_{index}"] = dict(block)
    # The json round-trip flattens f90nml's OrderedDicts and numpy scalars
    # into plain Python types.
    return json.loads(json.dumps(plain))


class NamelistFileHandler:
    """Read and write Fortran namelist files using f90nml.

    Fortran namelists are named blocks (`&block_name ... /`) containing
    key-value pairs. JULES uses roughly 30 separate namelist files to organize
    its parameters by physical process and model component.

    This handler converts namelist contents to standard Python dicts (rather
    than `OrderedDict`) for cleaner pretty-printing, since Python 3.7+ dicts
    guarantee insertion order.

    ## Repeated groups

    Fortran lets one group appear several times in a file, and JULES relies on
    it: `jules_output_profile` occurs `nprofiles` times, and so on for the rest
    of `julesconf.schemas.REPEATABLE_GROUPS`. `f90nml` represents this
    inconsistently — a bare `Namelist` for a single occurrence, a `Cogroup` for
    several, and `_grp_<name>_<n>` keys once `todict()` flattens it — so this
    handler normalises it away at the boundary:

    - `read` returns a `list[dict]` for every repeatable group, of length one
      when the file had one occurrence, and never emits a `_grp_` key;
    - `write` emits one Fortran group per list entry, via `add_cogroup`.

    Downstream, a repeated group is simply a list of blocks, in both the
    schemas and the TOML forms, and the empty list means no groups at all.
    """

    def read(self, path: str | PathLike) -> dict:
        """Read a Fortran namelist file and return its contents as a dict.

        Args:
            path: Path to the `.nml` file to read.

        Returns:
            A nested dict containing all namelist blocks and their key-value
            pairs. Top-level keys correspond to namelist block names; a
            repeatable group maps to a list of block dicts, one per occurrence.
        """
        return namelist_to_dict(f90nml.read(path))

    def write(
        self, path: str | PathLike, data: dict, *, overwrite_ok: bool = False
    ) -> None:
        """Write a dict to a Fortran namelist file.

        Args:
            path: Path to the `.nml` file to write.
            data: A nested dict containing namelist blocks and their key-value
                pairs. Top-level keys become namelist block names. A value that
                is a list of dicts is written as that many repetitions of the
                group, so an empty list writes no group at all.
            overwrite_ok: If `True`, overwrite an existing file at `path`.
                If `False` (default), `f90nml` will raise an error if the
                file already exists.
        """
        namelist = f90nml.Namelist()
        for group, value in data.items():
            if isinstance(value, list):
                for block in value:
                    namelist.add_cogroup(group, block)
            else:
                namelist[group] = value
        f90nml.write(namelist, path, force=overwrite_ok)


@dataclasses.dataclass
class NamelistConfig(DirConfig):
    """Configuration for a JULES namelists directory.

    Contains all 29 required namelist files, each with a fixed `.nml` path
    and handled by `NamelistFileHandler`.

    This class is instantiated without arguments, since all field defaults are
    fully specified:

        namelists = NamelistConfig()
        data = namelists.read("/path/to/namelists")
    """

    ancillaries: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("ancillaries.nml", NamelistFileHandler),
    )
    """Ancillary data namelist."""

    crop_params: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("crop_params.nml", NamelistFileHandler),
    )
    """Crop parameters namelist."""

    drive: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("drive.nml", NamelistFileHandler),
    )
    """Driving data configuration namelist.

    Controls meteorological forcing data: start/end dates, time step,
    variable names, and path to the driving data file.
    """

    fire: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("fire.nml", NamelistFileHandler),
    )
    """Fire parameters namelist."""

    imogen: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("imogen.nml", NamelistFileHandler),
    )
    """IMOGEN configuration namelist."""

    initial_conditions: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("initial_conditions.nml", NamelistFileHandler),
    )
    """Initial conditions namelist."""

    jules_deposition: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_deposition.nml", NamelistFileHandler),
    )
    """Deposition parameters namelist."""

    jules_hydrology: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_hydrology.nml", NamelistFileHandler),
    )
    """Hydrology parameters namelist."""

    jules_irrig: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_irrig.nml", NamelistFileHandler),
    )
    """Irrigation parameters namelist."""

    jules_prnt_control: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_prnt_control.nml", NamelistFileHandler),
    )
    """Print control namelist."""

    jules_radiation: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_radiation.nml", NamelistFileHandler),
    )
    """Radiation parameters namelist."""

    jules_rivers: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_rivers.nml", NamelistFileHandler),
    )
    """River routing parameters namelist."""

    jules_snow: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_snow.nml", NamelistFileHandler),
    )
    """Snow parameters namelist."""

    jules_soil_biogeochem: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_soil_biogeochem.nml", NamelistFileHandler),
    )
    """Soil biogeochemistry parameters namelist."""

    jules_soil: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_soil.nml", NamelistFileHandler),
    )
    """Soil parameters namelist."""

    jules_surface: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_surface.nml", NamelistFileHandler),
    )
    """Surface parameters namelist."""

    jules_surface_types: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_surface_types.nml", NamelistFileHandler),
    )
    """Surface types namelist."""

    jules_vegetation: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_vegetation.nml", NamelistFileHandler),
    )
    """Vegetation parameters namelist."""

    jules_water_resources: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("jules_water_resources.nml", NamelistFileHandler),
    )
    """Water resources namelist."""

    model_environment: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("model_environment.nml", NamelistFileHandler),
    )
    """Model environment namelist."""

    model_grid: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("model_grid.nml", NamelistFileHandler),
    )
    """Model grid configuration namelist."""

    nveg_params: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("nveg_params.nml", NamelistFileHandler),
    )
    """Non-vegetated surface parameters namelist."""

    output: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("output.nml", NamelistFileHandler),
    )
    """Output configuration namelist."""

    pft_params: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("pft_params.nml", NamelistFileHandler),
    )
    """Plant functional type parameters namelist."""

    prescribed_data: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("prescribed_data.nml", NamelistFileHandler),
    )
    """Prescribed data namelist."""

    science_fixes: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("science_fixes.nml", NamelistFileHandler),
    )
    """Science fixes namelist."""

    timesteps: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("timesteps.nml", NamelistFileHandler),
    )
    """Timestep configuration namelist."""

    triffid_params: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("triffid_params.nml", NamelistFileHandler),
    )
    """TRIFFID dynamic vegetation parameters namelist."""

    urban: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("urban.nml", NamelistFileHandler),
    )
    """Urban parameters namelist."""


@dirconf.filter(write=lambda path, data, **_: not path.is_absolute())
@dirconf.filter_missing()
class AsciiFileHandler:
    """Read and write floating-point ASCII data files using numpy.

    JULES uses plain-text ASCII files for input data such as initial conditions
    and tile fraction maps. Comment lines starting with `#` or `!` are
    preserved and returned alongside the numeric data.

    The write filter ensures that only relative paths are accepted, preventing
    accidental writes to absolute paths. Missing files are handled gracefully
    rather than raising an error immediately.
    """

    class AsciiData(TypedDict):
        """Container for ASCII file data with values array and comment header.

        Attributes:
            values: A 1D or 2D numpy array of floating-point values. Single-row
                data is always returned as shape `(1, n)` for consistency.
            comment: The comment header from the file, with all comment lines
                joined by newlines.
        """

        values: numpy.ndarray
        comment: str

    def read(self, path: str | PathLike) -> AsciiData:
        """Read an ASCII file and return its numeric values and comment header.

        Lines beginning with `#` or `!` are treated as comments. All comment
        lines at the start of the file are collected and returned as a single
        string. The remaining lines are parsed as numeric data.

        Single-row data is reshaped from 1D to 2D with shape `(1, n)` to
        ensure round-trip consistency with `numpy.savetxt`.

        Args:
            path: Path to the ASCII file to read.

        Returns:
            An `AsciiData` dict containing:

            - `values`: A numpy array of the numeric data.
            - `comment`: The collected comment header as a string.
        """
        comment_lines = []
        num_lines = 0
        with open(path) as file:
            for line in file:
                line = line.strip()
                if line.startswith(("#", "!")):
                    comment_lines.append(line)
                    continue
                elif line:
                    num_lines = num_lines + 1
                    if num_lines > 1:
                        break
        comment = "\n".join(comment_lines)
        values = numpy.loadtxt(str(path), comments=("#", "!"))
        if num_lines == 1:
            assert values.ndim == 1
            values = values.reshape(1, -1)
        return self.AsciiData(values=values, comment=comment)

    def write(
        self, path: str | PathLike, data: AsciiData, *, overwrite_ok: bool = False
    ) -> None:
        """Write an `AsciiData` dict to an ASCII file.

        Values are written with `%.5f` formatting. The comment string is
        written as a header with `#` prefix on each line.

        Args:
            path: Path to the ASCII file to write.
            data: An `AsciiData` dict with `values` (numpy array) and
                `comment` (string header).
            overwrite_ok: If `True`, overwrite an existing file at `path`.
                If `False` (default), `numpy.savetxt` will raise an error
                if the file already exists.
        """
        numpy.savetxt(
            str(path),
            data["values"],
            fmt="%.5f",
            header=data["comment"],
            comments="#",
        )


# NOTE: @dirconf.filter does not preserve __module__, fix it manually.
# See: https://github.com/jmarshrossney/dirconf/issues/XX
AsciiFileHandler.__module__ = __name__


@dirconf.filter(
    read=lambda path: not path.is_absolute(),
    write=lambda path, data, **_: not path.is_absolute(),
)
@dirconf.filter_missing()
class NetcdfFileHandler:
    """Read and write NetCDF datasets using xarray.

    NetCDF is the preferred format for large multidimensional time series such
    as meteorological driving data. It is compact, self-describing, and supports
    metadata and coordinate labels natively.

    The read and write filters ensure that only relative paths are accepted,
    preventing accidental access to absolute paths. Missing files are handled
    gracefully rather than raising an error immediately.
    """

    def read(self, path: str | PathLike) -> xarray.Dataset:
        """Read a NetCDF file and return a fully loaded xarray Dataset.

        The entire dataset is loaded into memory via `xarray.load_dataset`.
        For very large files, consider using `xarray.open_dataset` with lazy
        loading instead.

        Args:
            path: Path to the NetCDF file to read.

        Returns:
            An `xarray.Dataset` containing all variables, coordinates, and
            attributes from the file.
        """
        return xarray.load_dataset(path)

    def write(
        self,
        path: str | PathLike,
        data: xarray.Dataset,
        *,
        overwrite_ok: bool = False,
    ) -> None:
        """Write an xarray Dataset to a NetCDF file.

        Args:
            path: Path to the NetCDF file to write.
            data: An `xarray.Dataset` to serialize.
            overwrite_ok: If `True`, overwrite an existing file at `path`.
                If `False` (default), raises `FileExistsError` if the file
                already exists.

        Raises:
            FileExistsError: If `overwrite_ok` is `False` and a file
                already exists at `path`.
        """
        if not overwrite_ok and Path(path).is_file():
            raise FileExistsError(f"There is already a file at '{path}'")
        data.to_netcdf(path)


# NOTE: @dirconf.filter does not preserve __module__, fix it manually.
# See: https://github.com/jmarshrossney/dirconf/issues/XX
NetcdfFileHandler.__module__ = __name__


dirconf.register_handler("ascii", AsciiFileHandler, [".txt", ".dat", ".asc"])
dirconf.register_handler("netcdf", NetcdfFileHandler, [".nc", ".cdf"])


@dataclasses.dataclass
class InputFilesConfig(DirConfig):
    """Configuration for JULES input data files.

    Contains nodes for initial conditions, tile fractions, and driving
    (meteorological forcing) data. Paths are resolved at instantiation time.

    Initial conditions and tile fractions are expected to be ASCII files,
    while driving data can be either ASCII or NetCDF (handler inferred by
    file extension).

    Example:
        inputs = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="Loobos_1997.nc",
        )
    """

    initial_conditions: Node = dataclasses.field(
        metadata={"transform": path_to_node(AsciiFileHandler)},
    )
    """Initial conditions file.

    Specifies the starting state of soil moisture, temperature, and other
    prognostic variables at each grid point. Expected to be an ASCII file.
    """

    tile_fractions: Node = dataclasses.field(
        metadata={"transform": path_to_node(AsciiFileHandler)},
    )
    """Tile fractions file.

    Defines the fractional coverage of each surface type (e.g., broadleaf
    trees, C3 grass, urban) within a grid cell. Expected to be an ASCII file.
    """

    driving_data: Node = dataclasses.field(
        metadata={"transform": to_node},
    )
    """Driving (meteorological forcing) data file.

    Contains time series of meteorological variables (temperature,
    precipitation, radiation, etc.) that force the model. Handler is
    inferred from the file extension (`.dat`/`.txt` for ASCII,
    `.nc`/`.cdf` for NetCDF).
    """


@dataclasses.dataclass
class JulesConfig(DirConfig):
    """Top-level configuration for the JULES land surface model.

    Combines a namelists directory (with all required `.nml` files) and
    an input data directory (with driving data, initial conditions, and
    tile fractions).

    The `namelists` field is fully fixed since all namelist file paths
    are known in advance. The `inputs` field is resolved at instantiation
    time, allowing different file paths to be bound for different runs.

    Example:
        config = JulesConfig(
            namelists="namelists",
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        config_dict = config.read("/path/to/jules/config")
    """

    inputs: Node = dataclasses.field(
        metadata={"transform": to_node},
    )
    """Input data directory.

    Should be configured with an `InputFilesConfig` handler at
    instantiation time to specify the exact file paths for initial
    conditions, tile fractions, and driving data.
    """

    namelists: Node = dataclasses.field(
        init=False,
        default_factory=lambda: Node("namelists", NamelistConfig),
    )
    """Namelists directory.

    Contains all 29 required JULES namelist files, each with a fixed
    `.nml` path. Handled by `NamelistConfig`.
    """
