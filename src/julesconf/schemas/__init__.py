"""Pydantic validation schemas for JULES namelist files.

Each module corresponds to one JULES namelist file and exposes a top-level
model named after the file (e.g. ``TimestepsNamelist`` for ``timesteps.nml``).
Call ``Model.model_validate(data)`` where ``data`` is the dict returned by
reading the file with :class:`~julesconf.config.NamelistFileHandler`.

The top-level :class:`~julesconf.schemas.namelists.JulesNamelists` model
validates a complete namelists directory (output of
:meth:`~julesconf.config.NamelistConfig.read`), including cross-namelist
consistency checks.
"""

from julesconf.schemas.namelists import JulesNamelists

__all__ = ["JulesNamelists"]
