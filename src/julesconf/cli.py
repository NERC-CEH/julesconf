"""The `julesconf` command-line interface.

A thin shell over `julesconf.schemas.JulesNamelists` and `julesconf.rose`, so
that validating a configuration or converting between the three file forms
does not require writing any Python:

    julesconf validate          <namelists-dir | config.toml> [--strict]
    julesconf convert rose2nml  <rose-app.conf>  -o <dir>
    julesconf convert rose2toml <rose-app.conf>  -o <config.toml>
    julesconf convert toml2nml  <config.toml>    -o <dir>
    julesconf convert nml2toml  <namelists-dir>  -o <config.toml>

Exit codes are stable, so the tool can be dropped into a CI pipeline or a
pre-submission check:

| `0` | success                                                |
|-----|--------------------------------------------------------|
| `1` | the configuration is invalid, or conversion failed     |
| `2` | the command line itself was wrong                      |

Validation failures are rendered by `julesconf._errors`, which locates each
one as `file.nml  BLOCK  member` rather than as a pydantic model path.
Warnings are grouped by category and labelled with whether they are advisory
or mean part of the configuration is silently dropped.
"""

from __future__ import annotations

import enum
import tempfile
import warnings
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console

from julesconf._errors import (
    WarningGroup,
    format_validation_error,
    format_warnings,
    group_warnings,
)
from julesconf.rose import NamelistFiles, RoseApp, rose_to_namelists
from julesconf.schemas import JulesNamelists

__all__ = ["app"]

app = typer.Typer(
    name="julesconf",
    help="Validate and convert JULES model configurations.",
    no_args_is_help=True,
    add_completion=False,
)

convert_app = typer.Typer(
    name="convert",
    help="Convert between JULES configuration formats.",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(convert_app)

# Rich turns colour off by itself when the stream is not a terminal, so the
# same code is safe interactively and in a pipeline. Markup, highlighting and
# wrapping are all off: the reports contain literal brackets and quotes that
# rich would otherwise eat, and `julesconf._errors` has already wrapped them.
_KWARGS = {"markup": False, "highlight": False, "soft_wrap": True}
out = Console(**_KWARGS)  # type: ignore[arg-type]
err = Console(stderr=True, **_KWARGS)  # type: ignore[arg-type]


class OnUnbound(enum.StrEnum):
    """What to do with an environment variable the app does not bind."""

    keep = "keep"
    error = "error"
    empty = "empty"


def _version_callback(value: bool) -> None:
    """Print the installed version and exit."""
    if not value:
        return
    try:
        installed = _package_version("julesconf")
    except PackageNotFoundError:  # pragma: no cover - only if run from source
        installed = "unknown"
    out.print(f"julesconf {installed}")
    raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
) -> None:
    """Validate and convert JULES model configurations."""


# ----------------------------------------------------------------------
# Reporting helpers
# ----------------------------------------------------------------------


def _report_validation_error(exc: ValidationError) -> None:
    """Print a located, readable report for a validation failure."""
    err.print(format_validation_error(exc), style="red")


def _report_warnings(groups: list[WarningGroup], *, quiet: bool) -> None:
    """Print grouped warnings, loudest category first.

    Args:
        groups: The groups to report.
        quiet: If `True`, drop the advisory categories and keep only the ones
            that mean part of the configuration is being discarded.
    """
    if quiet:
        groups = [group for group in groups if group.kind.is_data_loss]
    if not groups:
        return
    style = "yellow" if any(group.kind.is_data_loss for group in groups) else "dim"
    err.print(format_warnings(groups), style=style)


def _report_unresolved(files: NamelistFiles, on_unbound: OnUnbound) -> None:
    """Name the environment variables the app left unresolved.

    A rose app is not self-contained: `$DUMP_FILE`, `$LOOBOS_INSTALL_DIR` and
    friends come from the cylc workflow. Under the default `keep` they survive
    into the output verbatim and then fail validation as a nonsensical path,
    so say plainly what happened instead of letting it look like a mystery.
    """
    if not files.unresolved:
        return

    names = sorted(files.unresolved)
    err.print(
        f"Unresolved environment variables ({len(names)}):",
        style="bold yellow",
    )
    for name in names:
        err.print(f"  ${name}", style="yellow")

    consequence = (
        "Left in the output verbatim. Any path containing one will fail "
        "validation as a bad path."
        if on_unbound is OnUnbound.keep
        else "Replaced with the empty string, so paths may be truncated."
    )
    err.print(
        "\nThese are supplied by the cylc workflow, not by the app. "
        f"{consequence}\nSet them in the environment before converting, or "
        "choose a different --on-unbound mode.\n",
        style="yellow",
    )


def _fail(message: str) -> typer.Exit:
    """Print an error and return the exit-1 exception to raise."""
    err.print(f"Error: {message}", style="bold red")
    return typer.Exit(1)


def _check_output(path: Path, overwrite: bool) -> None:
    """Refuse to clobber an existing output file unless asked to.

    Raises:
        typer.Exit: If the file exists and `overwrite` is `False`.
    """
    if path.exists() and not overwrite:
        raise _fail(f"{path} already exists; pass --overwrite to replace it")


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------


def _load(target: Path, *, strict: bool) -> tuple[JulesNamelists, list[WarningGroup]]:
    """Read a config from a namelists directory or a TOML file.

    Args:
        target: A directory of `.nml` files, or a `.toml` file.
        strict: Escalate julesconf's warnings to errors.

    Returns:
        The validated config and the warnings raised while reading it.

    Raises:
        typer.Exit: With code 2 if `target` is neither form, or code 1 if the
            config is invalid.
    """
    if target.is_dir():
        read = JulesNamelists.from_namelists
    elif target.suffix == ".toml":
        read = JulesNamelists.from_toml
    else:
        raise typer.BadParameter(
            f"{target} is neither a namelists directory nor a .toml file"
        )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            config = read(target, strict=strict)
        except ValidationError as exc:
            _report_warnings(group_warnings(caught), quiet=False)
            _report_validation_error(exc)
            raise typer.Exit(1) from None
        except Warning as exc:
            # `strict` turns julesconf's own warnings into raised warnings.
            _report_warnings(group_warnings(caught), quiet=False)
            raise _fail(f"{type(exc).__name__}: {exc}") from None
        except (ValueError, OSError) as exc:
            raise _fail(f"{type(exc).__name__}: {exc}") from None

    return config, group_warnings(caught)


def _convert_rose(conf: Path, on_unbound: OnUnbound) -> NamelistFiles:
    """Read a rose app and convert it to namelist text.

    Raises:
        typer.Exit: With code 1 if the app cannot be interpreted.
    """
    try:
        return rose_to_namelists(RoseApp.parse_file(conf), on_unbound=on_unbound.value)
    except (ValueError, OSError) as exc:
        raise _fail(f"{type(exc).__name__}: {exc}") from None


def _write_namelists(files: NamelistFiles, directory: Path, overwrite: bool) -> None:
    """Write converted namelist text into a directory.

    Raises:
        typer.Exit: With code 1 if a target file exists and `overwrite` is
            `False`.
    """
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(
        str(directory / name) for name in files if (directory / name).exists()
    )
    if existing and not overwrite:
        raise _fail(
            f"refusing to overwrite {len(existing)} file(s) in {directory}; "
            "pass --overwrite"
        )
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8")


def _write_toml(config: JulesNamelists, path: Path, *, flat: bool) -> None:
    """Write a validated config to a TOML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    config.to_toml(path, grouped=not flat)


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------

_Strict = Annotated[
    bool,
    typer.Option(
        "--strict",
        help="Treat julesconf's warnings as errors — anything it cannot represent.",
    ),
]
_Quiet = Annotated[
    bool,
    typer.Option(
        "--quiet",
        "-q",
        help="Suppress advisory output. Data-loss warnings are still shown.",
    ),
]
_Flat = Annotated[
    bool,
    typer.Option(
        "--flat",
        help="Write the flat TOML form, mirroring the namelists, "
        "instead of the grouped [[pft]] form.",
    ),
]
_Overwrite = Annotated[
    bool, typer.Option("--overwrite", help="Overwrite existing output files.")
]
_OnUnbound = Annotated[
    OnUnbound,
    typer.Option(
        "--on-unbound",
        help="What to do with an environment variable the app does not bind.",
    ),
]


@app.command()
def validate(
    target: Annotated[
        Path,
        typer.Argument(
            exists=True,
            help="A namelists directory, or a .toml config file.",
        ),
    ],
    strict: _Strict = False,
    quiet: _Quiet = False,
) -> None:
    """Validate a JULES configuration.

    The argument may be a directory of `.nml` files or a `.toml` config in
    either form; which one it is is detected from the path.
    """
    config, groups = _load(target, strict=strict)
    _report_warnings(groups, quiet=quiet)
    if not quiet:
        surface = config.jules_surface_types.jules_surface_types
        out.print(
            f"{target} is valid "
            f"(npft={surface.npft}, ncpft={surface.ncpft}, nnvg={surface.nnvg}).",
            style="green",
        )


@convert_app.command()
def rose2nml(
    conf: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, help="Path to a rose-app.conf."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Destination namelists directory."),
    ],
    on_unbound: _OnUnbound = OnUnbound.keep,
    overwrite: _Overwrite = False,
    quiet: _Quiet = False,
) -> None:
    """Convert a rose app into a directory of Fortran namelist files."""
    files = _convert_rose(conf, on_unbound)
    _write_namelists(files, output, overwrite)
    _report_unresolved(files, on_unbound)
    if not quiet:
        out.print(
            f"Wrote {len(files)} namelist file(s) to {output}.",
            style="green",
        )


@convert_app.command()
def rose2toml(
    conf: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, help="Path to a rose-app.conf."),
    ],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Destination .toml file.")
    ],
    flat: _Flat = False,
    on_unbound: _OnUnbound = OnUnbound.keep,
    strict: _Strict = False,
    overwrite: _Overwrite = False,
    quiet: _Quiet = False,
) -> None:
    """Convert a rose app into a single validated TOML config.

    The app is first converted to namelists, exactly as `rose2nml` does, then
    read and validated, then written back out as TOML.
    """
    _check_output(output, overwrite)
    files = _convert_rose(conf, on_unbound)
    _report_unresolved(files, on_unbound)

    with tempfile.TemporaryDirectory() as staged:
        _write_namelists(files, Path(staged), overwrite=True)
        config, groups = _load(Path(staged), strict=strict)

    _report_warnings(groups, quiet=quiet)
    _write_toml(config, output, flat=flat)
    if not quiet:
        form = "flat" if flat else "grouped"
        out.print(f"Wrote {form} TOML config to {output}.", style="green")


@convert_app.command()
def toml2nml(
    config_file: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, help="Path to a .toml config."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Destination namelists directory."),
    ],
    strict: _Strict = False,
    overwrite: _Overwrite = False,
    quiet: _Quiet = False,
) -> None:
    """Write the namelist files a TOML config describes.

    Every member julesconf holds a default for is written explicitly, so the
    resulting namelists fully determine the run.
    """
    config, groups = _load(config_file, strict=strict)
    _report_warnings(groups, quiet=quiet)
    try:
        config.to_namelists(output, overwrite_ok=overwrite)
    except (OSError, ValueError) as exc:
        raise _fail(f"{type(exc).__name__}: {exc}") from None
    if not quiet:
        out.print(f"Wrote namelists to {output}.", style="green")


@convert_app.command()
def nml2toml(
    namelists: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, help="A directory of .nml files."),
    ],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Destination .toml file.")
    ],
    flat: _Flat = False,
    strict: _Strict = False,
    overwrite: _Overwrite = False,
    quiet: _Quiet = False,
) -> None:
    """Read a namelists directory and write it out as a TOML config."""
    _check_output(output, overwrite)
    config, groups = _load(namelists, strict=strict)
    _report_warnings(groups, quiet=quiet)
    _write_toml(config, output, flat=flat)
    if not quiet:
        form = "flat" if flat else "grouped"
        out.print(f"Wrote {form} TOML config to {output}.", style="green")
