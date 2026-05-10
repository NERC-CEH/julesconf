"""Top-level ``JulesNamelists`` schema combining all 29 namelist files.

Usage::

    from julesconf.config import NamelistConfig
    from julesconf.schemas.namelists import JulesNamelists

    data = NamelistConfig().read("/path/to/jules/namelists")
    JulesNamelists.model_validate(data)
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from julesconf.schemas.ancillaries import AncillariesNamelist
from julesconf.schemas.crop_params import CropParamsNamelist
from julesconf.schemas.drive import DriveNamelist
from julesconf.schemas.fire import FireNamelist
from julesconf.schemas.imogen import ImogenNamelist
from julesconf.schemas.initial_conditions import InitialConditionsNamelist
from julesconf.schemas.jules_deposition import JulesDepositionNamelist
from julesconf.schemas.jules_hydrology import JulesHydrologyNamelist
from julesconf.schemas.jules_irrig import JulesIrrigNamelist
from julesconf.schemas.jules_prnt_control import JulesPrntControlNamelist
from julesconf.schemas.jules_radiation import JulesRadiationNamelist
from julesconf.schemas.jules_rivers import JulesRiversNamelist
from julesconf.schemas.jules_snow import JulesSnowNamelist
from julesconf.schemas.jules_soil import JulesSoilNamelist
from julesconf.schemas.jules_soil_biogeochem import JulesSoilBiogeochemNamelist
from julesconf.schemas.jules_surface import JulesSurfaceNamelist
from julesconf.schemas.jules_surface_types import JulesSurfaceTypesNamelist
from julesconf.schemas.jules_vegetation import JulesVegetationNamelist
from julesconf.schemas.jules_water_resources import JulesWaterResourcesNamelist
from julesconf.schemas.model_environment import ModelEnvironmentNamelist
from julesconf.schemas.model_grid import ModelGridNamelist
from julesconf.schemas.nveg_params import NvegParamsNamelist
from julesconf.schemas.output import OutputNamelist
from julesconf.schemas.pft_params import PftParamsNamelist
from julesconf.schemas.prescribed_data import PrescribedDataNamelist
from julesconf.schemas.science_fixes import ScienceFixesNamelist
from julesconf.schemas.timesteps import TimestepsNamelist
from julesconf.schemas.triffid_params import TriffidParamsNamelist
from julesconf.schemas.urban import UrbanNamelist

__all__ = ["JulesNamelists"]


class JulesNamelists(BaseModel):
    """Schema for a complete JULES namelists directory.

    Validates a dict of the form returned by
    :meth:`~julesconf.config.NamelistConfig.read`, applying both
    per-namelist constraints and cross-namelist consistency checks.
    """

    model_config = ConfigDict(extra="ignore")

    ancillaries: AncillariesNamelist = AncillariesNamelist()
    crop_params: CropParamsNamelist = CropParamsNamelist()
    drive: DriveNamelist
    fire: FireNamelist = FireNamelist()
    imogen: ImogenNamelist = ImogenNamelist()
    initial_conditions: InitialConditionsNamelist
    jules_deposition: JulesDepositionNamelist = JulesDepositionNamelist()
    jules_hydrology: JulesHydrologyNamelist
    jules_irrig: JulesIrrigNamelist = JulesIrrigNamelist()
    jules_prnt_control: JulesPrntControlNamelist = JulesPrntControlNamelist()
    jules_radiation: JulesRadiationNamelist
    jules_rivers: JulesRiversNamelist = JulesRiversNamelist()
    jules_snow: JulesSnowNamelist = JulesSnowNamelist()
    jules_soil: JulesSoilNamelist
    jules_soil_biogeochem: JulesSoilBiogeochemNamelist = Field(
        default_factory=JulesSoilBiogeochemNamelist
    )
    jules_surface: JulesSurfaceNamelist
    jules_surface_types: JulesSurfaceTypesNamelist
    jules_vegetation: JulesVegetationNamelist
    jules_water_resources: JulesWaterResourcesNamelist = JulesWaterResourcesNamelist()
    model_environment: ModelEnvironmentNamelist
    model_grid: ModelGridNamelist = ModelGridNamelist()
    nveg_params: NvegParamsNamelist
    output: OutputNamelist = OutputNamelist()
    pft_params: PftParamsNamelist
    prescribed_data: PrescribedDataNamelist = PrescribedDataNamelist()
    science_fixes: ScienceFixesNamelist = ScienceFixesNamelist()
    timesteps: TimestepsNamelist
    triffid_params: TriffidParamsNamelist = TriffidParamsNamelist()
    urban: UrbanNamelist = UrbanNamelist()

    @model_validator(mode="after")
    def _check_pft_list_lengths(self) -> "JulesNamelists":
        npft = self.jules_surface_types.jules_surface_types.npft
        pftparm = self.pft_params.jules_pftparm
        for field_name, value in pftparm.model_dump().items():
            if isinstance(value, list) and len(value) != npft:
                raise ValueError(
                    f"pft_params.jules_pftparm.{field_name} has"
                    f" {len(value)} element(s), expected npft={npft}"
                )
        return self

    @model_validator(mode="after")
    def _check_nveg_list_lengths(self) -> "JulesNamelists":
        nnvg = self.jules_surface_types.jules_surface_types.nnvg
        nvegparm = self.nveg_params.jules_nvegparm
        for field_name, value in nvegparm.model_dump().items():
            if isinstance(value, list) and len(value) != nnvg:
                raise ValueError(
                    f"nveg_params.jules_nvegparm.{field_name} has"
                    f" {len(value)} element(s), expected nnvg={nnvg}"
                )
        return self

    @model_validator(mode="after")
    def _check_snow_npft_lists(self) -> "JulesNamelists":
        npft = self.jules_surface_types.jules_surface_types.npft
        snow = self.jules_snow.jules_snow
        for field_name in (
            "cansnowpft",
            "can_clump",
            "n_lai_exposed",
            "lai_alb_lim_sn",
            "unload_rate_cnst",
            "unload_rate_u",
        ):
            value = getattr(snow, field_name)
            if value is not None and len(value) != npft:
                raise ValueError(
                    f"jules_snow.jules_snow.{field_name} has"
                    f" {len(value)} element(s), expected npft={npft}"
                )
        return self
