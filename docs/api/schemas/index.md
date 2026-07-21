# Schemas

Pydantic validation schemas for JULES namelist files, pinned to the
[JULES v7.9 user guide](https://jules-lsm.github.io/user_guide/doc/source/namelists/).

There is one module per `.nml` file, named after it, each exposing a top-level
model named after the file plus one model per namelist block it contains.
[`JulesNamelists`](namelists.md) combines all 29 and adds the cross-namelist
consistency checks that no single file can make on its own.

## Usage

Validate a whole namelists directory:

```python
from julesconf.config import NamelistConfig
from julesconf.schemas import JulesNamelists, JULES_VERSION

data = NamelistConfig().read("/path/to/jules/namelists")
model = JulesNamelists.model_validate(data)
```

...or a single file, if that is all you have:

```python
from julesconf.schemas.timesteps import TimestepsNamelist

TimestepsNamelist.model_validate(data["timesteps"])
```

Note that per-file validation cannot check list lengths against `npft` / `nnvg`,
since those are declared in `jules_surface_types.nml`.

## Coverage

| File | Model | Configures |
| --- | --- | --- |
| [`ancillaries.nml`](ancillaries.md) | `AncillariesNamelist` | Spatially varying ancillary fields (surface fractions, soil properties, topography) |
| [`crop_params.nml`](crop_params.md) | `CropParamsNamelist` | Per-crop-type parameters; needed when `ncpft > 0` |
| [`drive.nml`](drive.md) | `DriveNamelist` | Meteorological driving data input |
| [`fire.nml`](fire.md) | `FireNamelist` | Wildfire calculations |
| [`imogen.nml`](imogen.md) | `ImogenNamelist` | The IMOGEN climate emulator |
| [`initial_conditions.nml`](initial_conditions.md) | `InitialConditionsNamelist` | Initial state of the prognostic variables |
| [`jules_deposition.nml`](jules_deposition.md) | `JulesDepositionNamelist` | Dry deposition of atmospheric trace constituents |
| [`jules_hydrology.nml`](jules_hydrology.md) | `JulesHydrologyNamelist` | Hydrology options |
| [`jules_irrig.nml`](jules_irrig.md) | `JulesIrrigNamelist` | Irrigation options |
| [`jules_prnt_control.nml`](jules_prnt_control.md) | `JulesPrntControlNamelist` | Diagnostic and informative message output |
| [`jules_radiation.nml`](jules_radiation.md) | `JulesRadiationNamelist` | Radiation options |
| [`jules_rivers.nml`](jules_rivers.md) | `JulesRiversNamelist` | River routing and overbank inundation |
| [`jules_snow.nml`](jules_snow.md) | `JulesSnowNamelist` | Snow options and parameters |
| [`jules_soil.nml`](jules_soil.md) | `JulesSoilNamelist` | Soil options and parameters |
| [`jules_soil_biogeochem.nml`](jules_soil_biogeochem.md) | `JulesSoilBiogeochemNamelist` | Soil biogeochemistry (single-pool, 4-pool or ECOSSE) |
| [`jules_surface.nml`](jules_surface.md) | `JulesSurfaceNamelist` | Surface exchange options |
| [`jules_surface_types.nml`](jules_surface_types.md) | `JulesSurfaceTypesNamelist` | The surface types themselves — source of `npft`, `nnvg`, `ncpft` |
| [`jules_vegetation.nml`](jules_vegetation.md) | `JulesVegetationNamelist` | Vegetation and photosynthesis options |
| [`jules_water_resources.nml`](jules_water_resources.md) | `JulesWaterResourcesNamelist` | Water resource management |
| [`model_environment.nml`](model_environment.md) | `ModelEnvironmentNamelist` | How JULES is being run, and which land surface model |
| [`model_grid.nml`](model_grid.md) | `ModelGridNamelist` | Input grid, model grid, land fraction and coordinates |
| [`nveg_params.nml`](nveg_params.md) | `NvegParamsNamelist` | Per-non-vegetation-type parameters (length `nnvg`) |
| [`output.nml`](output.md) | `OutputNamelist` | Output profiles and variables |
| [`pft_params.nml`](pft_params.md) | `PftParamsNamelist` | Per-plant-functional-type parameters (length `npft`) |
| [`prescribed_data.nml`](prescribed_data.md) | `PrescribedDataNamelist` | Time-varying prescribed input data |
| [`science_fixes.nml`](science_fixes.md) | `ScienceFixesNamelist` | Switches for bug fixes that change results |
| [`timesteps.nml`](timesteps.md) | `TimestepsNamelist` | Timestep length, run period and spin-up |
| [`triffid_params.nml`](triffid_params.md) | `TriffidParamsNamelist` | Parameters for the TRIFFID dynamic vegetation model |
| [`urban.nml`](urban.md) | `UrbanNamelist` | The two-tile urban scheme |

The `cable_*` namelists, `jules_soil_ecosse.nml`, `oasis_rivers.nml` and
`red_params.nml` documented in the user guide do **not** yet have schemas. See
[field constraints](constraints.md) for the vocabulary to write one.

## Behaviour notes

- **Unknown keys:** every model emits a `UnknownNamelistKeyWarning` when it
  encounters a namelist member it does not recognise. This surfaces typos
  (which JULES itself silently ignores) without rejecting configs that contain
  members the schema does not yet cover. To escalate warnings to hard errors:

      import warnings
      from julesconf.schemas import UnknownNamelistKeyWarning

      warnings.simplefilter("error", UnknownNamelistKeyWarning)

- **Sentinel values:** many real-valued fields accept `-1.0` as a JULES sentinel
  meaning "use the default".

- **List lengths:** fields whose length is tied to `npft`, `nnvg`, `ncpft` or
  `ntype` are marked with `ListLen` and checked by
  [`JulesNamelists`](namelists.md), not by the per-file model.
