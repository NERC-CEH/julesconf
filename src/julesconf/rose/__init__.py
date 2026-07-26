"""Support for the Met Office "rose" configuration files used to drive JULES.

The `rose-app.conf` files in the JULES repository are the canonical form of a
JULES configuration for anyone working inside the Met Office suite ecosystem.
This subpackage lets julesconf read them.

`RoseConfig` is the format layer only: it parses and writes the rose INI
dialect and leaves every value as raw text. Nothing in it is specific to
JULES.
"""

from julesconf.rose._config import (
    RoseConfig,
    RoseParseError,
    Section,
    Setting,
    State,
)

__all__ = [
    "RoseConfig",
    "RoseParseError",
    "Section",
    "Setting",
    "State",
]
