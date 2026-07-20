"""Top-level ``JulesNamelists`` schema combining all 29 namelist files.

Usage::

    from julesconf.config import NamelistConfig
    from julesconf.schemas.namelists import JulesNamelists

    data = NamelistConfig().read("/path/to/jules/namelists")
    JulesNamelists.model_validate(data)
"""

from pydantic import Field, model_validator

from julesconf.schemas._base import NamelistModel
from julesconf.schemas._utils import ListLen
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


class JulesNamelists(NamelistModel):
    """Schema for a complete JULES namelists directory.

    Validates a dict of the form returned by
    :meth:`~julesconf.config.NamelistConfig.read`, applying both
    per-namelist constraints and cross-namelist consistency checks.
    """

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
    def _check_list_lengths(self) -> "JulesNamelists":
        _targets = [
            "triffid_params.jules_triffid",
            "crop_params.jules_cropparm",
            "pft_params.jules_pftparm",
            "nveg_params.jules_nvegparm",
            "jules_snow.jules_snow",
            "jules_deposition.jules_deposition_species",
        ]
        dims = {
            "npft": self.jules_surface_types.jules_surface_types.npft,
            "nnvg": self.jules_surface_types.jules_surface_types.nnvg,
            "ncpft": self.jules_surface_types.jules_surface_types.ncpft,
            "ntype": (
                self.jules_surface_types.jules_surface_types.npft
                + self.jules_surface_types.jules_surface_types.nnvg
            ),
        }
        for path in _targets:
            submodel = self
            for attr in path.split("."):
                submodel = getattr(submodel, attr)
            for field_name, field_info in type(submodel).model_fields.items():
                for meta in field_info.metadata:
                    if isinstance(meta, ListLen):
                        value = getattr(submodel, field_name)
                        if isinstance(value, list) and len(value) != dims[meta.dim]:
                            raise ValueError(
                                f"{path}.{field_name} has {len(value)} element(s),"
                                f" expected {meta.dim}={dims[meta.dim]}"
                            )
        return self
