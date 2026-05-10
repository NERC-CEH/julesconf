"""Validation schema for ``jules_irrig.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/jules_irrig.nml.rst``
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["JulesIrrigNamelist"]


class JulesIrrig(BaseModel):
    """``JULES_IRRIG`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_irrig_dmd: bool = False
    """Switch controlling the implementation of irrigation demand code."""
    l_irrig_limit: bool = False
    """Switch controlling whether water used for irrigation is limited by available supply."""
    irr_crop: Literal[0, 1, 2] = 0
    """Irrigation season determination: 0 = year-round, 1 = from driving data (Döll & Siebert), 2 = by maximum DVI (requires ``ncpft`` > 0)."""
    frac_irrig_all_tiles: bool = True
    """If TRUE, irrigation fraction is applied to all tiles; if FALSE, only to tiles listed in ``irrigtiles``."""
    set_irrfrac_on_irrtiles: bool = False
    """If TRUE, irrigation fraction is applied as specified on individual tiles; if FALSE, as a gridbox average."""
    nirrtile: int | None = Field(default=None, ge=1)
    """Number of surface tiles to irrigate; required if ``frac_irrig_all_tiles`` = FALSE."""
    irrigtiles: list[int] | None = None
    """Indices of surface tiles to irrigate; required if ``frac_irrig_all_tiles`` = FALSE."""
    nstep_irrig: int | None = Field(default=None, ge=1)
    """Number of model timesteps between irrigation updates; defaults to once per day."""

    @model_validator(mode="after")
    def _check_irrigtiles_length(self) -> "JulesIrrig":
        if (
            self.irrigtiles is not None
            and self.nirrtile is not None
            and len(self.irrigtiles) != self.nirrtile
        ):
            raise ValueError(
                f"irrigtiles has {len(self.irrigtiles)} element(s),"
                f" expected nirrtile={self.nirrtile}"
            )
        return self


class JulesIrrigNamelist(BaseModel):
    """Top-level schema for ``jules_irrig.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_irrig: JulesIrrig = JulesIrrig()
