"""Pydantic validation schemas for JULES namelist files.

Each module corresponds to one JULES namelist file and exposes a top-level
model named after the file (e.g. ``TimestepsNamelist`` for ``timesteps.nml``).
Call ``Model.model_validate(data)`` where ``data`` is the dict returned by
reading the file with :class:`~julesconf.config.NamelistFileHandler`.
"""
