"""Validation schema for ``ancillaries.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/ancillaries.nml.rst``
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["AncillariesNamelist"]


def _check_nvars_lists(obj: BaseModel, nvars_val: int) -> None:
    """Raise ValueError if any provided list has wrong length vs nvars."""
    for name in ("var", "use_file", "const_val", "var_name"):
        val = getattr(obj, name, None)
        if val is not None and len(val) != nvars_val:
            raise ValueError(
                f"{name} has {len(val)} element(s), expected nvars={nvars_val}"
            )
    if nvars_val > 0 and getattr(obj, "var", None) is None:
        raise ValueError("var is required when nvars > 0")


class JulesFrac(BaseModel):
    """``JULES_FRAC`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    file: str | None = None
    """The name of the file to read surface type fractional coverage data from."""
    read_from_dump: bool = False
    """Populate variables from dump file if TRUE, otherwise use other namelist members."""


class _NvarsModel(BaseModel):
    """Mixin for namelists with nvars/var/use_file/const_val pattern."""

    model_config = ConfigDict(extra="ignore")

    nvars: int = Field(default=0, ge=0)
    """The number of vegetation property variables that will be provided."""
    var: list[str] | None = None
    """List of vegetation variable names as recognised by JULES."""
    use_file: list[bool] | None = None
    """Indicates if variable should be read from file or set to constant value."""
    const_val: list[float] | None = None
    """Constant value that variable will be set to at every point."""
    var_name: list[str] | None = None
    """The name of the variable in the file containing the data."""
    file: str | None = None
    """The name of the file to read surface type fractional coverage data from."""
    read_from_dump: bool = False
    """Populate variables from dump file if TRUE, otherwise use other namelist members."""
    const_z: bool = False
    """Switch indicating if soil properties are uniform with depth."""

    @model_validator(mode="after")
    def _check_lists(self) -> "_NvarsModel":
        _check_nvars_lists(self, self.nvars)
        return self


class JulesSoilProps(_NvarsModel):
    """``JULES_SOIL_PROPS`` namelist members."""


class JulesTop(_NvarsModel):
    """``JULES_TOP`` namelist members."""


class JulesAgric(BaseModel):
    """``JULES_AGRIC`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    l_triffid_agric: bool = False


class JulesVegetationProps(_NvarsModel):
    """``JULES_VEGETATION_PROPS`` namelist members."""


class JulesPdm(_NvarsModel):
    """``JULES_PDM`` namelist members."""


class JulesCropProps(_NvarsModel):
    """``JULES_CROP_PROPS`` namelist members."""


class JulesIrrigProps(_NvarsModel):
    """``JULES_IRRIG_PROPS`` namelist members."""


class JulesRiversProps(BaseModel):
    """``JULES_RIVERS_PROPS`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class JulesWaterResourcesProps(_NvarsModel):
    """``JULES_WATER_RESOURCES_PROPS`` namelist members."""


class UrbanProperties(_NvarsModel):
    """``URBAN_PROPERTIES`` namelist members."""


class JulesCo2(BaseModel):
    """``JULES_CO2`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    co2_mmr: float | None = None
    """Concentration of atmospheric CO2 as mass mixing ratio."""


class JulesOverbankProps(BaseModel):
    """``JULES_OVERBANK_PROPS`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class JulesFlake(_NvarsModel):
    """``JULES_FLAKE`` namelist members."""


class AncillariesNamelist(BaseModel):
    """Top-level schema for ``ancillaries.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_frac: JulesFrac = JulesFrac()
    jules_vegetation_props: JulesVegetationProps = JulesVegetationProps()
    jules_soil_props: JulesSoilProps = JulesSoilProps()
    jules_top: JulesTop = JulesTop()
    jules_pdm: JulesPdm = JulesPdm()
    jules_agric: JulesAgric = JulesAgric()
    jules_crop_props: JulesCropProps = JulesCropProps()
    jules_irrig_props: JulesIrrigProps = JulesIrrigProps()
    jules_rivers_props: JulesRiversProps = JulesRiversProps()
    jules_water_resources_props: JulesWaterResourcesProps = JulesWaterResourcesProps()
    urban_properties: UrbanProperties = UrbanProperties()
    jules_co2: JulesCo2 = JulesCo2()
    jules_overbank_props: JulesOverbankProps = JulesOverbankProps()
    jules_flake: JulesFlake = JulesFlake()
