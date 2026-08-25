r"""Parser and serialiser for the Met Office "rose" configuration file format.

This module is a pure format layer: it knows nothing about JULES. It reads
and writes the modified INI dialect used by `rose-app.conf` and
`rose-meta.conf` files, leaving every value as raw, uninterpreted text.

The format
----------

A rose config is a sequence of *settings* (`key=value`), optionally grouped
into *sections* (`[name]`). Settings that appear before the first section
header are "root" settings, e.g. the `meta=jules-standalone/vn7.9` line at
the top of a `rose-app.conf`.

Both sections and settings carry a *state*: normal, user-ignored (`!`) or
system-ignored (`!!`). The marker is a prefix, so `[!!namelist:cable_pftparm]`
is a system-ignored section and `!!a1gs_io=17*9.0` is a system-ignored
setting.

A line whose first character is `#` is a comment. Comments are attached to
the section or setting they immediately precede, and a blank line clears any
comment not yet attached. Trailing comments do not exist: a `#` part-way
through a line is just part of the value.

A line beginning with whitespace continues the previous setting. The
continuation is joined to the value with a newline; if the continuation
begins with `=` once its indentation is removed, that single `=` is dropped.
So:

    var='b','sathh','satcon',
       ='hcon','albsoil'

has the value `"'b','sathh','satcon',\n'hcon','albsoil'"`.

Values are never interpreted. They routinely contain Fortran literal syntax
(`.false.`, `'./output'`, `8*'S'`, `0.28e6`) which downstream layers pass
through verbatim.

Example:
    config = RoseConfig.parse_file("rose-app.conf")
    config.sections["namelist:jules_soil"].settings["dzsoil_io"].value
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from os import PathLike
from typing import Self

__all__ = [
    "RoseConfig",
    "RoseParseError",
    "Section",
    "Setting",
    "State",
]

_SECTION_RE = re.compile(r"^\s*\[(?P<state>!?!?)(?P<name>.*)\]\s*$")
_SETTING_RE = re.compile(r"^(?P<state>!?!?)(?P<key>[^\s=]+)\s*=\s*(?P<value>.*)$")

_COMMENT_CHAR = "#"
_ASSIGN_CHAR = "="


class State(StrEnum):
    """Whether a section or setting is enabled, and if not, who disabled it.

    The value of each member is the literal prefix used in the file, which
    makes the enum directly usable when writing a line out.
    """

    NORMAL = ""
    """Enabled. No prefix."""

    USER_IGNORED = "!"
    """Disabled by a user, written as a single `!` prefix."""

    SYST_IGNORED = "!!"
    """Disabled by rose itself (e.g. by a trigger), written as `!!`."""


class RoseParseError(ValueError):
    """A line of a rose config file could not be parsed.

    Attributes:
        line_number: One-based index of the offending line.
        line: The offending line, without its trailing newline.
    """

    def __init__(self, line_number: int, line: str, message: str) -> None:
        """Initialise the error.

        Args:
            line_number: One-based index of the offending line.
            line: The offending line, without its trailing newline.
            message: Human-readable description of the problem.
        """
        super().__init__(f"line {line_number}: {message}: {line!r}")
        self.line_number = line_number
        self.line = line


@dataclass
class Setting:
    r"""A single `key=value` entry.

    Attributes:
        value: The raw text of the value, never interpreted or normalised.
            Multi-line values (written as continuation lines) are joined
            with `\n`.
        state: Whether the setting is enabled, and if not, who disabled it.
        comments: Comment lines immediately preceding the setting, each
            stored without its leading `#`.
    """

    value: str = ""
    state: State = State.NORMAL
    comments: list[str] = field(default_factory=list)


@dataclass
class Section:
    """A `[name]` section and the settings it contains.

    The section name itself is the key under which the section is stored in
    `RoseConfig.sections`, so it is not repeated here.

    Attributes:
        state: Whether the section is enabled, and if not, who disabled it.
        settings: The settings declared in the section, in declaration order.
        comments: Comment lines immediately preceding the section header,
            each stored without its leading `#`.
    """

    state: State = State.NORMAL
    settings: dict[str, Setting] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)


@dataclass
class RoseConfig:
    """A parsed rose configuration file.

    Attributes:
        root: Settings declared before the first section header, in
            declaration order.
        sections: Sections, keyed by name, in declaration order.
        comments: Comment lines at the very top of the file, separated from
            the rest by a blank line, each stored without its leading `#`.
    """

    root: dict[str, Setting] = field(default_factory=dict)
    sections: dict[str, Section] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse the contents of a rose config file.

        A repeated section header adds to the section already declared,
        updating its state; a repeated key replaces the earlier setting while
        keeping its position in the declaration order.

        Args:
            text: The full text of the file.

        Returns:
            The parsed configuration.

        Raises:
            RoseParseError: If a line is neither blank, a comment, a section
                header, a continuation, nor a `key=value` setting.
        """
        config = cls()
        section: Section | None = None
        setting: Setting | None = None
        pending: list[str] = []

        def end_comment_block() -> None:
            """Dispose of comments not followed by a section or setting.

            A comment block at the very top of the file describes the file
            itself. Anywhere else there is nothing for such comments to attach
            to, and rose has no way to represent them, so they are dropped.
            """
            nonlocal pending
            if pending and not (config.root or config.sections or config.comments):
                config.comments.extend(pending)
            pending = []

        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                end_comment_block()
                continue

            if line.lstrip().startswith(_COMMENT_CHAR):
                pending.append(line.strip()[1:])
                continue

            if setting is not None and line[0].isspace():
                continuation = line.strip()
                if continuation.startswith(_ASSIGN_CHAR):
                    continuation = continuation[1:]
                setting.value = f"{setting.value}\n{continuation}"
                continue

            match = _SECTION_RE.match(line)
            if match is not None:
                name = match["name"].strip()
                state = State(match["state"])
                setting = None
                if not name:
                    # An empty header, `[]`, returns to the root of the file.
                    section = None
                elif (existing := config.sections.get(name)) is not None:
                    existing.state = state
                    existing.comments.extend(pending)
                    section = existing
                else:
                    section = Section(state=state, comments=list(pending))
                    config.sections[name] = section
                pending = []
                continue

            match = _SETTING_RE.match(line)
            if match is None:
                raise RoseParseError(line_number, line, "not a section or setting")
            setting = Setting(
                value=match["value"].strip(),
                state=State(match["state"]),
                comments=list(pending),
            )
            target = config.root if section is None else section.settings
            target[match["key"]] = setting
            pending = []

        end_comment_block()
        return config

    @classmethod
    def parse_file(cls, path: str | PathLike) -> Self:
        """Parse a rose config file from disk.

        Args:
            path: Path to the file, e.g. a `rose-app.conf` or
                `rose-meta.conf`.

        Returns:
            The parsed configuration.

        Raises:
            RoseParseError: If a line cannot be parsed.
        """
        with open(path, encoding="utf-8") as file:
            return cls.parse(file.read())

    def dump(self) -> str:
        """Serialise back to rose config text.

        julesconf does not ship or generate rose configs, so this exists
        mainly to make `parse` testable: dumping a parsed file reproduces it
        byte for byte, which is a far stronger check on the parser than
        inspecting the parsed structure.

        Sections and settings are written in declaration order rather than
        sorted, so a file that rose itself wrote comes back unchanged.

        Returns:
            The full text of the file, ending in a newline unless the
            configuration is empty.
        """
        lines: list[str] = []
        blank_line_needed = False

        lines.extend(f"{_COMMENT_CHAR}{comment}" for comment in self.comments)
        blank_line_needed = bool(self.comments)

        if self.root:
            if blank_line_needed:
                lines.append("")
            blank_line_needed = True
            for key, setting in self.root.items():
                lines.extend(_setting_lines(key, setting))

        for name, section in self.sections.items():
            if blank_line_needed:
                lines.append("")
            blank_line_needed = True
            lines.extend(f"{_COMMENT_CHAR}{comment}" for comment in section.comments)
            lines.append(f"[{section.state}{name}]")
            for key, setting in section.settings.items():
                lines.extend(_setting_lines(key, setting))

        if not lines:
            return ""
        return "\n".join(lines) + "\n"


def _setting_lines(key: str, setting: Setting) -> list[str]:
    """Render one setting, with its comments, as a list of lines.

    Continuation lines are indented so that their `=` sits directly under the
    `=` of the first line, which is the convention rose itself writes.

    Args:
        key: The setting's key.
        setting: The setting to render.

    Returns:
        The lines to write, without trailing newlines.
    """
    prefix = f"{setting.state}{key}"
    head, *tail = setting.value.split("\n")
    indent = " " * len(prefix)
    return [
        *(f"{_COMMENT_CHAR}{comment}" for comment in setting.comments),
        f"{prefix}{_ASSIGN_CHAR}{head}",
        *(f"{indent}{_ASSIGN_CHAR}{line}" for line in tail),
    ]
