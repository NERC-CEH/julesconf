"""Validation schema for `jules_irrig.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/jules_irrig.nml.rst`
"""

from enum import IntEnum
from typing import Annotated

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import name_or_value

__all__ = ["IrrCrop", "JulesIrrigNamelist"]


class IrrCrop(IntEnum):
    """Irrigation season determination (`irr_crop`)."""

    year_round = 0
    driving_data = 1
    max_dvi = 2


class JulesIrrig(NamelistModel):
    """`JULES_IRRIG` namelist members."""

    l_irrig_dmd: bool = False
    """Switch controlling the implementation of irrigation demand code."""
    l_irrig_limit: bool = False
    """Switch controlling whether water used for irrigation is limited by available supply."""
    irr_crop: Annotated[IrrCrop, name_or_value(IrrCrop)] = IrrCrop.year_round
    """Irrigation season determination: `year_round` (0), `driving_data` (1, Döll & Siebert), `max_dvi` (2, requires `ncpft` > 0)."""
    frac_irrig_all_tiles: bool = True
    """If TRUE, irrigation fraction is applied to all tiles; if FALSE, only to tiles listed in `irrigtiles`."""
    set_irrfrac_on_irrtiles: bool = False
    """If TRUE, irrigation fraction is applied as specified on individual tiles; if FALSE, as a gridbox average."""
    nirrtile: int | None = Field(default=None, ge=1)
    """Number of surface tiles to irrigate; required if `frac_irrig_all_tiles` = FALSE."""
    irrigtiles: list[int] | None = None
    """Indices of surface tiles to irrigate; required if `frac_irrig_all_tiles` = FALSE."""
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


class JulesIrrigNamelist(NamelistModel):
    """Top-level schema for `jules_irrig.nml`."""

    jules_irrig: JulesIrrig = JulesIrrig()
