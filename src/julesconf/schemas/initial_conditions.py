"""Validation schema for ``initial_conditions.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/initial_conditions.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["InitialConditionsNamelist"]


class JulesInitial(BaseModel):
    """``JULES_INITIAL`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    dump_file: bool = False
    total_snow: bool = False
    l_broadcast_soilt: bool = False
    file: str | None = None

    nvars: int = Field(default=0, ge=0)
    var: list[str] | None = None
    use_file: list[bool] | None = None
    const_val: list[float] | None = None
    var_name: list[str] | None = None

    @model_validator(mode="after")
    def _check_var_lists(self) -> "JulesInitial":
        if self.nvars > 0:
            if self.var is None:
                raise ValueError("var is required when nvars > 0")
            if len(self.var) != self.nvars:
                raise ValueError(
                    f"var has {len(self.var)} element(s), expected nvars={self.nvars}"
                )
            if self.use_file is not None and len(self.use_file) != self.nvars:
                raise ValueError(
                    f"use_file has {len(self.use_file)} element(s),"
                    f" expected nvars={self.nvars}"
                )
            if self.const_val is not None and len(self.const_val) != self.nvars:
                raise ValueError(
                    f"const_val has {len(self.const_val)} element(s),"
                    f" expected nvars={self.nvars}"
                )
        return self


class InitialConditionsNamelist(BaseModel):
    """Top-level schema for ``initial_conditions.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_initial: JulesInitial
