"""Support for the Met Office "rose" configuration files used to drive JULES.

The `rose-app.conf` files in the JULES repository are the canonical form of a
JULES configuration for anyone working inside the Met Office suite ecosystem.
This subpackage lets julesconf read them.

`RoseConfig` is the format layer only: it parses and writes the rose INI
dialect and leaves every value as raw text. Nothing in it is specific to
JULES.

`RoseApp` adds the JULES interpretation: the `meta=` declaration, the
`[file:…]` sections and their `source=` lists, and the `[namelist:…]`
sections themselves. `rose_to_namelists` then converts an app to the
Fortran namelist files it describes.

Conversion is one-way. julesconf reads rose apps but never writes them.
"""

from julesconf.rose._app import (
    MissingNamelistError,
    RoseApp,
    RoseAppError,
    SourceRef,
    UnboundVariableError,
    UnsupportedSourceError,
)
from julesconf.rose._config import (
    RoseConfig,
    RoseParseError,
    Section,
    Setting,
    State,
)
from julesconf.rose.convert import (
    NamelistFiles,
    expand_env,
    rose_app_to_namelists,
    rose_to_namelists,
)

__all__ = [
    "MissingNamelistError",
    "NamelistFiles",
    "RoseApp",
    "RoseAppError",
    "RoseConfig",
    "RoseParseError",
    "Section",
    "Setting",
    "SourceRef",
    "State",
    "UnboundVariableError",
    "UnsupportedSourceError",
    "expand_env",
    "rose_app_to_namelists",
    "rose_to_namelists",
]
