"""Top-level `JulesNamelists` schema combining all 29 namelist files.

Usage:

    from julesconf.config import NamelistConfig
    from julesconf.schemas import JulesNamelists

    data = NamelistConfig().read("/path/to/jules/namelists")
    JulesNamelists.model_validate(data)
"""

from typing import Any, get_args

from pydantic import model_validator
from pydantic.fields import FieldInfo

from julesconf.schemas._base import NamelistModel
from julesconf.schemas.ancillaries import AncillariesNamelist
from julesconf.schemas.constraints import ListLen
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


def find_list_len(field_info: FieldInfo) -> ListLen | None:
    """Return the `ListLen` metadata for a field, if it has any.

    Pydantic only surfaces metadata from the outermost `Annotated` in
    `FieldInfo.metadata`, so `Annotated[list[X], ListLen(...)] | None`
    hides the marker inside a union member. This searches the full annotation
    so both that spelling and the canonical
    `Annotated[list[X] | None, ListLen(...)]` resolve.

    Args:
        field_info: The Pydantic field to inspect.

    Returns:
        The first `ListLen` found, or `None` if the field has none.
    """
    for meta in field_info.metadata:
        if isinstance(meta, ListLen):
            return meta
    return _find_in_annotation(field_info.annotation)


def _find_in_annotation(annotation: Any) -> ListLen | None:
    """Recursively search an annotation's type arguments for a `ListLen`."""
    for arg in get_args(annotation):
        if isinstance(arg, ListLen):
            return arg
        found = _find_in_annotation(arg)
        if found is not None:
            return found
    return None


class JulesNamelists(NamelistModel):
    """Schema for a complete JULES namelists directory.

    Validates a dict of the form returned by
    `julesconf.config.NamelistConfig.read`, applying both
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
    jules_soil_biogeochem: JulesSoilBiogeochemNamelist = JulesSoilBiogeochemNamelist()
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
        """Check every `ListLen`-marked list against its dimension.

        Walks the whole model tree rather than a fixed set of namelists, so a
        `ListLen` field added anywhere is checked automatically.
        """
        surface_types = self.jules_surface_types.jules_surface_types
        dims = {
            "npft": surface_types.npft,
            "nnvg": surface_types.nnvg,
            "ncpft": surface_types.ncpft,
            "ntype": surface_types.npft + surface_types.nnvg,
        }
        self._check_model_list_lengths(self, "", dims)
        return self

    @staticmethod
    def _check_model_list_lengths(
        model: NamelistModel, path: str, dims: dict[str, int]
    ) -> None:
        """Recursively validate `ListLen` fields on `model` and its submodels."""
        for field_name, field_info in type(model).model_fields.items():
            value = getattr(model, field_name)
            field_path = f"{path}.{field_name}" if path else field_name

            if isinstance(value, NamelistModel):
                JulesNamelists._check_model_list_lengths(value, field_path, dims)
                continue

            meta = find_list_len(field_info)
            if (
                meta is not None
                and isinstance(value, list)
                and len(value) != dims[meta.dim]
            ):
                raise ValueError(
                    f"{field_path} has {len(value)} element(s),"
                    f" expected {meta.dim}={dims[meta.dim]}"
                )
