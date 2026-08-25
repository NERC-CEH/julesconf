r"""The JULES-shaped view of a parsed rose configuration.

`RoseConfig` is a pure format layer: it knows about sections, settings and
states, but not about what any of them mean. This module adds the JULES
interpretation on top, splitting a parsed `rose-app.conf` into the three
kinds of section a JULES app contains:

- `[command]`, naming the executable to run (julesconf ignores it);
- `[file:<target>]`, each holding a single `source=` setting that lists,
  in order, the namelist sections to write into `<target>`;
- `[namelist:<block>]`, holding the settings themselves. A block may be
  *indexed*, written `[namelist:<block>(N)]`, when JULES expects a
  repeated group (output profiles, deposition species, prescribed
  datasets).

The `source=` grammar
---------------------

`source=` is a whitespace-separated list of tokens:

| `namelist:X`    | required; the section must exist            |
| `(namelist:X)`  | optional; skipped if absent or ignored      |
| `namelist:X(:)` | every indexed section `X(1)`, `X(2)`, …     |

Rose also supports `fs:`, `svn:` and `git:` source schemes. No JULES app in
`rose-stem/app/` uses them, and julesconf could not honour them offline
anyway, so any other scheme raises `UnsupportedSourceError` rather than
being silently dropped.

Example:
    app = RoseApp.parse_file("rose-app.conf")
    app.files["model_grid.nml"][0].block
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from os import PathLike
from typing import Self

from julesconf.rose._config import RoseConfig, Section, State

__all__ = [
    "MissingNamelistError",
    "RoseApp",
    "RoseAppError",
    "SourceRef",
    "UnboundVariableError",
    "UnsupportedSourceError",
]

COMMAND_SECTION = "command"
"""Name of the section naming the executable to run."""

FILE_PREFIX = "file:"
"""Prefix marking a section that describes an output file."""

NAMELIST_PREFIX = "namelist:"
"""Prefix marking a section that holds namelist settings."""

SOURCE_KEY = "source"
"""The only setting julesconf reads from a `[file:…]` section."""

INDEXED_SUFFIX = "(:)"
"""Suffix on a `source=` token meaning "every indexed section"."""

_INDEX_RE = re.compile(r"^(?P<block>.+)\((?P<index>\d+)\)$")


class RoseAppError(ValueError):
    """Base class for problems interpreting a rose app as a JULES config."""


class UnsupportedSourceError(RoseAppError):
    """A `source=` token names something other than a namelist section.

    Attributes:
        token: The offending token, as written in the file.
        target: The file the token was listed for.
    """

    def __init__(self, token: str, target: str) -> None:
        """Initialise the error.

        Args:
            token: The offending token, as written in the file.
            target: The file the token was listed for.
        """
        super().__init__(
            f"[{FILE_PREFIX}{target}] source token {token!r} is not a "
            f"'{NAMELIST_PREFIX}' source; julesconf only converts namelists"
        )
        self.token = token
        self.target = target


class MissingNamelistError(RoseAppError):
    """A required `source=` token names a section that is not in the app.

    Attributes:
        block: The missing block name, without its `namelist:` prefix.
        target: The file the token was listed for.
    """

    def __init__(self, block: str, target: str) -> None:
        """Initialise the error.

        Args:
            block: The missing block name, without its `namelist:` prefix.
            target: The file the token was listed for.
        """
        super().__init__(
            f"[{FILE_PREFIX}{target}] requires section "
            f"[{NAMELIST_PREFIX}{block}], which the app does not define"
        )
        self.block = block
        self.target = target


class UnboundVariableError(RoseAppError):
    """A value references an environment variable with no value.

    Raised only under `on_unbound="error"`, which reproduces what rose
    itself does. The other modes keep or blank the reference instead.

    Attributes:
        name: The name of the unbound variable, without its `$`.
    """

    def __init__(self, name: str) -> None:
        """Initialise the error.

        Args:
            name: The name of the unbound variable, without its `$`.
        """
        super().__init__(f"unbound environment variable: ${name}")
        self.name = name


@dataclass(frozen=True)
class SourceRef:
    """One token of a `[file:…]` section's `source=` list.

    Attributes:
        block: The referenced block name, without its `namelist:` prefix and
            without any `(:)` suffix.
        optional: Whether the token was parenthesised, meaning the section
            may be absent or ignored.
        indexed: Whether the token carried the `(:)` suffix, meaning it
            stands for every indexed section of that block.
    """

    block: str
    optional: bool = False
    indexed: bool = False

    @classmethod
    def parse(cls, token: str, target: str = "") -> Self:
        """Parse a single `source=` token.

        Args:
            token: The token as written, e.g. `namelist:jules_soil`,
                `(namelist:jules_top)` or `namelist:jules_output_profile(:)`.
            target: The file the token was listed for, used only in error
                messages.

        Returns:
            The parsed reference.

        Raises:
            UnsupportedSourceError: If the token is not a `namelist:` source.
        """
        name = token
        optional = name.startswith("(") and name.endswith(")")
        if optional:
            name = name[1:-1]
        if not name.startswith(NAMELIST_PREFIX):
            raise UnsupportedSourceError(token, target)
        name = name[len(NAMELIST_PREFIX) :]
        indexed = name.endswith(INDEXED_SUFFIX)
        if indexed:
            name = name[: -len(INDEXED_SUFFIX)]
        return cls(block=name, optional=optional, indexed=indexed)


@dataclass
class RoseApp:
    """A `rose-app.conf` read as a JULES configuration.

    Sections whose state is not normal are dropped on the way in for
    `[file:…]` sections — an ignored output file is simply not written —
    but kept for `[namelist:…]` sections, since whether a referenced
    section is ignored changes how a `source=` token behaves.

    Attributes:
        meta: The value of the root `meta=` setting, e.g.
            `jules-standalone/vn8.2`, or `None` if the app has none.
        command: The contents of the `[command]` section, as raw text.
            julesconf does not run JULES, so this is recorded and ignored.
        files: The output files to write, keyed by target name, each mapped
            to its `source=` list in declaration order.
        namelists: The namelist sections, keyed by block name without the
            `namelist:` prefix. Indexed sections keep their index, so the
            keys look like `jules_output_profile(1)`.
    """

    meta: str | None = None
    command: dict[str, str] = field(default_factory=dict)
    files: dict[str, list[SourceRef]] = field(default_factory=dict)
    namelists: dict[str, Section] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: RoseConfig) -> Self:
        """Interpret an already-parsed rose config as a JULES app.

        Args:
            config: The parsed configuration.

        Returns:
            The JULES-shaped view of it.

        Raises:
            UnsupportedSourceError: If a `source=` token is not a
                `namelist:` source.
        """
        app = cls()

        meta = config.root.get("meta")
        if meta is not None and meta.state is State.NORMAL:
            app.meta = meta.value

        for name, section in config.sections.items():
            if name == COMMAND_SECTION:
                app.command = {
                    key: setting.value for key, setting in section.settings.items()
                }
            elif name.startswith(FILE_PREFIX):
                if section.state is not State.NORMAL:
                    continue
                target = name[len(FILE_PREFIX) :]
                source = section.settings.get(SOURCE_KEY)
                tokens = source.value.split() if source is not None else []
                app.files[target] = [SourceRef.parse(token, target) for token in tokens]
            elif name.startswith(NAMELIST_PREFIX):
                app.namelists[name[len(NAMELIST_PREFIX) :]] = section

        return app

    @classmethod
    def parse_file(cls, path: str | PathLike) -> Self:
        """Read and interpret a `rose-app.conf` from disk.

        Args:
            path: Path to the file.

        Returns:
            The JULES-shaped view of it.

        Raises:
            RoseParseError: If a line cannot be parsed.
            UnsupportedSourceError: If a `source=` token is not a
                `namelist:` source.
        """
        return cls.from_config(RoseConfig.parse_file(path))

    def resolve(self, ref: SourceRef, target: str = "") -> list[str]:
        """Expand one `source=` token to the section keys it selects.

        Ignored sections are dropped, so a group is never emitted for a
        section the app has switched off. An indexed token expands to every
        matching section sorted by *numeric* index, so `(10)` follows `(2)`
        rather than preceding it.

        Args:
            ref: The reference to expand.
            target: The file the reference was listed for, used only in
                error messages.

        Returns:
            Keys into `namelists`, in the order they should be written.
            Possibly empty.

        Raises:
            MissingNamelistError: If a required, non-indexed section is
                absent from the app.
        """
        if ref.indexed:
            indexed: list[tuple[int, str]] = []
            for key, section in self.namelists.items():
                match = _INDEX_RE.match(key)
                if match is None or match["block"] != ref.block:
                    continue
                if section.state is not State.NORMAL:
                    continue
                indexed.append((int(match["index"]), key))
            return [key for _, key in sorted(indexed)]

        section = self.namelists.get(ref.block)
        if section is None:
            if ref.optional:
                return []
            raise MissingNamelistError(ref.block, target)
        if section.state is not State.NORMAL:
            return []
        return [ref.block]

    def sections_for(self, target: str) -> list[str]:
        """Expand a whole file's `source=` list.

        Args:
            target: The output file name, as it appears in `files`.

        Returns:
            Keys into `namelists`, in the order they should be written.

        Raises:
            KeyError: If the app does not describe that file.
            MissingNamelistError: If a required section is absent.
        """
        keys: list[str] = []
        for ref in self.files[target]:
            keys.extend(self.resolve(ref, target))
        return keys


def block_name(key: str) -> str:
    """Strip any `(N)` index from a namelist key.

    All indexed sections of a block are written out under the same Fortran
    group name; only their order distinguishes them.

    Args:
        key: A key of `RoseApp.namelists`, e.g. `jules_output_profile(2)`.

    Returns:
        The Fortran group name, e.g. `jules_output_profile`.
    """
    match = _INDEX_RE.match(key)
    return match["block"] if match is not None else key
