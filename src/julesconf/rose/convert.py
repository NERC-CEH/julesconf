r"""Convert a rose app into Fortran namelist files.

JULES's canonical configuration format inside the Met Office suite
ecosystem is a `rose-app.conf`; julesconf's schemas consume Fortran
namelists. This module bridges the two, reproducing what rose's own
namelist location handler does when it stages a JULES run.

The conversion is **one-way**. julesconf reads rose apps; it does not write
them. `rose namelist-dump` already exists upstream for the other direction.

The emission rules, which match rose's `NamelistLocHandler.pull`:

- groups are written in `source=` order;
- within a group, members are written in **sorted key order** — not the
  order they appear in the file;
- a setting whose state is not normal (`!` or `!!`) is skipped;
- an ignored section is omitted entirely, rather than emitted empty;
- a section with no live settings still emits an empty group, `&name` then
  `/`;
- each member is written `key=value,` — note the trailing comma — with the
  value copied **verbatim**. Rose never interprets values, and neither does
  this module: `8*'S'`, `5*1.667` and `0.28e6` reach the file unchanged.

Environment variables
---------------------

Rose apps are not self-contained. Values routinely reference variables
supplied by the cylc workflow rather than the app — `$LOOBOS_INSTALL_DIR`,
`$DUMP_FILE`, `$ROSE_TASK_NAME`. Rose hard-errors on an unbound variable,
which is useless for offline conversion, so `on_unbound` chooses:

| `"keep"`  | leave `$VAR` in the value (the default). The schema then |
|           | rejects it as a bad path, which is honest and traceable  |
| `"error"` | raise `UnboundVariableError`, as rose does               |
| `"empty"` | substitute the empty string                             |

Both `$VAR` and `${VAR}` are recognised, and a `\$` escape suppresses
substitution exactly as rose's `env_var_process` does.

Example:
    files = rose_to_namelists(RoseApp.parse_file("rose-app.conf"))
    files["model_grid.nml"]
    files.unresolved
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from typing import Literal

from julesconf.rose._app import (
    RoseApp,
    UnboundVariableError,
    block_name,
)
from julesconf.rose._config import State

__all__ = [
    "NamelistFiles",
    "expand_env",
    "rose_app_to_namelists",
    "rose_to_namelists",
]

OnUnbound = Literal["keep", "error", "empty"]
"""What to do with an environment variable that has no value."""

_ENV_RE = re.compile(
    r"(?P<escape>\\*)\$(?:\{(?P<braced>[A-Za-z_]\w*)\}|(?P<bare>[A-Za-z_]\w*))"
)


class NamelistFiles(dict[str, str]):
    """The converted files, plus a record of the environment lookups.

    This is a plain `{filename: text}` dict; the extra attributes let a
    caller report on substitution without a second pass over the app.

    Attributes:
        substituted: The variables that were resolved, mapped to the value
            used.
        unresolved: The names of variables that had no value, whatever
            `on_unbound` did about it.
    """

    def __init__(
        self,
        files: Mapping[str, str] = {},
        *,
        substituted: Mapping[str, str] | None = None,
        unresolved: set[str] | None = None,
    ) -> None:
        """Initialise the mapping.

        Args:
            files: The converted `{filename: text}` pairs.
            substituted: Variables resolved, mapped to the value used.
            unresolved: Names of variables that had no value.
        """
        super().__init__(files)
        self.substituted: dict[str, str] = dict(substituted or {})
        self.unresolved: set[str] = set(unresolved or ())


def expand_env(
    value: str,
    env: Mapping[str, str],
    *,
    on_unbound: OnUnbound = "keep",
    substituted: dict[str, str] | None = None,
    unresolved: set[str] | None = None,
) -> str:
    r"""Substitute `$VAR` and `${VAR}` references in a value.

    A reference preceded by an odd number of backslashes is escaped and
    left alone; as in rose, the run of backslashes is halved either way, so
    `\$X` becomes `$X` and `\\$X` becomes `\` followed by the value of `X`.

    Args:
        value: The raw value text.
        env: The environment to resolve against.
        on_unbound: What to do with a variable that `env` has no value for:
            `"keep"` leaves the reference verbatim, `"error"` raises, and
            `"empty"` substitutes the empty string.
        substituted: If given, updated with each variable resolved and the
            value used.
        unresolved: If given, updated with the name of each variable that
            had no value.

    Returns:
        The value with references substituted.

    Raises:
        UnboundVariableError: If `on_unbound` is `"error"` and a referenced
            variable has no value.
        ValueError: If `on_unbound` is not one of the three modes.
    """
    if on_unbound not in ("keep", "error", "empty"):
        raise ValueError(f"unknown on_unbound mode: {on_unbound!r}")

    def replace(match: re.Match[str]) -> str:
        escape = match["escape"]
        halved = "\\" * (len(escape) // 2)
        reference = match[0][len(escape) :]
        if len(escape) % 2:
            return halved + reference

        name = match["braced"] or match["bare"]
        if name in env:
            if substituted is not None:
                substituted[name] = env[name]
            return halved + env[name]

        if unresolved is not None:
            unresolved.add(name)
        if on_unbound == "error":
            raise UnboundVariableError(name)
        if on_unbound == "empty":
            return halved
        return halved + reference

    return _ENV_RE.sub(replace, value)


def rose_to_namelists(
    app: RoseApp,
    *,
    env: Mapping[str, str] | None = None,
    on_unbound: OnUnbound = "keep",
) -> NamelistFiles:
    """Convert a rose app to the text of the namelist files it describes.

    Args:
        app: The parsed app.
        env: The environment to resolve `$VAR` references against. Defaults
            to `os.environ`.
        on_unbound: What to do with a variable `env` has no value for. See
            `expand_env`.

    Returns:
        A `{filename: text}` mapping, in `[file:…]` declaration order, which
        also carries the `substituted` and `unresolved` variable records.

    Raises:
        MissingNamelistError: If a required section is absent from the app.
        UnboundVariableError: If `on_unbound` is `"error"` and a referenced
            variable has no value.
    """
    environment = os.environ if env is None else env
    substituted: dict[str, str] = {}
    unresolved: set[str] = set()

    files: dict[str, str] = {}
    for target in app.files:
        lines: list[str] = []
        for key in app.sections_for(target):
            section = app.namelists[key]
            lines.append(f"&{block_name(key)}")
            for member, setting in sorted(section.settings.items()):
                if setting.state is not State.NORMAL:
                    continue
                value = expand_env(
                    setting.value,
                    environment,
                    on_unbound=on_unbound,
                    substituted=substituted,
                    unresolved=unresolved,
                )
                lines.append(f"{member}={value},")
            lines.append("/")
        files[target] = "".join(f"{line}\n" for line in lines)

    return NamelistFiles(files, substituted=substituted, unresolved=unresolved)


def rose_app_to_namelists(
    conf_path: str | PathLike,
    directory: str | PathLike,
    *,
    env: Mapping[str, str] | None = None,
    on_unbound: OnUnbound = "keep",
    overwrite_ok: bool = False,
) -> NamelistFiles:
    """Convert a `rose-app.conf` on disk into a directory of `.nml` files.

    The files are written as text rather than round-tripped through
    `f90nml`, so values reach disk exactly as the app wrote them. The
    result is a namelists directory that `NamelistConfig.read` and
    `JulesNamelists.from_namelists` can consume — though a rose app
    typically describes more files than julesconf models, since it also
    covers the postponed `cable_*` namelists.

    Args:
        conf_path: Path to the `rose-app.conf`.
        directory: Destination directory; created if it does not exist.
        env: The environment to resolve `$VAR` references against. Defaults
            to `os.environ`.
        on_unbound: What to do with a variable `env` has no value for. See
            `expand_env`.
        overwrite_ok: If `True`, overwrite existing files in `directory`.

    Returns:
        The same mapping `rose_to_namelists` returns, so the caller can
        report on the substitutions made and the references left unresolved.

    Raises:
        FileExistsError: If `overwrite_ok` is `False` and a target file
            already exists.
        MissingNamelistError: If a required section is absent from the app.
        UnboundVariableError: If `on_unbound` is `"error"` and a referenced
            variable has no value.
    """
    files = rose_to_namelists(
        RoseApp.parse_file(conf_path), env=env, on_unbound=on_unbound
    )

    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)

    paths = {target: destination / target for target in files}
    if not overwrite_ok:
        existing = sorted(str(path) for path in paths.values() if path.exists())
        if existing:
            raise FileExistsError(f"refusing to overwrite: {', '.join(existing)}")

    for target, text in files.items():
        paths[target].write_text(text, encoding="utf-8")

    return files
