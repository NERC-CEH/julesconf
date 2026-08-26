# Configuration reference

One page per JULES namelist file, pinned to the [JULES v7.9 user guide](https://jules-lsm.github.io/user_guide/doc/source/namelists/).
Each page documents every member julesconf models: its type, bounds, permitted values and default.

There is one module per `.nml` file, named after it, each exposing a top-level model named after the file plus one model per namelist block it contains.
[`JulesNamelists`](../api/namelists.md) combines all 29 and adds the cross-namelist consistency checks no single file can make on its own.

## What do you want to set?

| To configure | Look in |
|---|---|
| Timestep length, run period, spin-up | [`timesteps.nml`](timesteps.md) |
| Which JULES this is, and which land surface model | [`model_environment.nml`](model_environment.md) |
| The grid, land fraction, coordinates | [`model_grid.nml`](model_grid.md) |
| Plant functional types and their parameters | [`jules_surface_types.nml`](jules_surface_types.md), [`pft_params.nml`](pft_params.md) |
| Crop types | [`crop_params.nml`](crop_params.md) |
| Non-vegetated surface types | [`nveg_params.nml`](nveg_params.md) |
| Dynamic vegetation (TRIFFID) | [`triffid_params.nml`](triffid_params.md), [`jules_vegetation.nml`](jules_vegetation.md) |
| Soil layers, hydraulics, bedrock | [`jules_soil.nml`](jules_soil.md) |
| Soil carbon and methane | [`jules_soil_biogeochem.nml`](jules_soil_biogeochem.md) |
| Runoff, water tables, river routing | [`jules_hydrology.nml`](jules_hydrology.md), [`jules_rivers.nml`](jules_rivers.md) |
| Driving data files and their variables | [`drive.nml`](drive.md) |
| Initial state of the prognostics | [`initial_conditions.nml`](initial_conditions.md) |
| Ancillary fields | [`ancillaries.nml`](ancillaries.md) |
| Time-varying prescribed inputs | [`prescribed_data.nml`](prescribed_data.md) |
| Output profiles and variables | [`output.nml`](output.md) |
| Diagnostic message verbosity | [`jules_prnt_control.nml`](jules_prnt_control.md) |

## By theme

### Run control

| File | Model | Configures |
| --- | --- | --- |
| [`model_environment.nml`](model_environment.md) | `ModelEnvironmentNamelist` | How JULES is being run, and which land surface model |
| [`timesteps.nml`](timesteps.md) | `TimestepsNamelist` | Timestep length, run period and spin-up |
| [`model_grid.nml`](model_grid.md) | `ModelGridNamelist` | Input grid, model grid, land fraction and coordinates |
| [`jules_prnt_control.nml`](jules_prnt_control.md) | `JulesPrntControlNamelist` | Diagnostic and informative message output |
| [`science_fixes.nml`](science_fixes.md) | `ScienceFixesNamelist` | Switches for bug fixes that change results |

### Surface types and vegetation

| File | Model | Configures |
| --- | --- | --- |
| [`jules_surface_types.nml`](jules_surface_types.md) | `JulesSurfaceTypesNamelist` | The surface types themselves — source of `npft`, `nnvg`, `ncpft` |
| [`pft_params.nml`](pft_params.md) | `PftParamsNamelist` | Per-plant-functional-type parameters (length `npft`) |
| [`crop_params.nml`](crop_params.md) | `CropParamsNamelist` | Per-crop-type parameters; needed when `ncpft > 0` |
| [`nveg_params.nml`](nveg_params.md) | `NvegParamsNamelist` | Per-non-vegetation-type parameters (length `nnvg`) |
| [`triffid_params.nml`](triffid_params.md) | `TriffidParamsNamelist` | Parameters for the TRIFFID dynamic vegetation model |
| [`jules_vegetation.nml`](jules_vegetation.md) | `JulesVegetationNamelist` | Vegetation and photosynthesis options |
| [`jules_surface.nml`](jules_surface.md) | `JulesSurfaceNamelist` | Surface exchange options |
| [`urban.nml`](urban.md) | `UrbanNamelist` | The two-tile urban scheme |

### Soil, water and snow

| File | Model | Configures |
| --- | --- | --- |
| [`jules_soil.nml`](jules_soil.md) | `JulesSoilNamelist` | Soil options and parameters |
| [`jules_soil_biogeochem.nml`](jules_soil_biogeochem.md) | `JulesSoilBiogeochemNamelist` | Soil biogeochemistry (single-pool, 4-pool or ECOSSE) |
| [`jules_hydrology.nml`](jules_hydrology.md) | `JulesHydrologyNamelist` | Hydrology options |
| [`jules_snow.nml`](jules_snow.md) | `JulesSnowNamelist` | Snow options and parameters |
| [`jules_rivers.nml`](jules_rivers.md) | `JulesRiversNamelist` | River routing and overbank inundation |
| [`jules_water_resources.nml`](jules_water_resources.md) | `JulesWaterResourcesNamelist` | Water resource management |
| [`jules_irrig.nml`](jules_irrig.md) | `JulesIrrigNamelist` | Irrigation options |

### Input data

| File | Model | Configures |
| --- | --- | --- |
| [`drive.nml`](drive.md) | `DriveNamelist` | Meteorological driving data input |
| [`initial_conditions.nml`](initial_conditions.md) | `InitialConditionsNamelist` | Initial state of the prognostic variables |
| [`ancillaries.nml`](ancillaries.md) | `AncillariesNamelist` | Spatially varying ancillary fields (surface fractions, soil properties, topography) |
| [`prescribed_data.nml`](prescribed_data.md) | `PrescribedDataNamelist` | Time-varying prescribed input data |

### Output

| File | Model | Configures |
| --- | --- | --- |
| [`output.nml`](output.md) | `OutputNamelist` | Output profiles and variables |

### Optional science

| File | Model | Configures |
| --- | --- | --- |
| [`jules_radiation.nml`](jules_radiation.md) | `JulesRadiationNamelist` | Radiation options |
| [`fire.nml`](fire.md) | `FireNamelist` | Wildfire calculations |
| [`jules_deposition.nml`](jules_deposition.md) | `JulesDepositionNamelist` | Dry deposition of atmospheric trace constituents |
| [`imogen.nml`](imogen.md) | `ImogenNamelist` | The IMOGEN climate emulator |

## Not modelled

Some user-guide namelists have no schema, for two different reasons.
`cable_*`, `oasis_rivers.nml` and `red_params.nml` are deliberately out of scope; others, such as `jules_soil_ecosse.nml`, are simply not written yet.
[Coverage and versions](../coverage.md) has the distinction and what each means for your config, and [adding a schema](../../develop/adding-a-schema.md) has the steps.

## Behaviour notes

- **Unknown keys.** Every model emits an `UnknownNamelistKeyWarning` for a member it does not recognise, which surfaces typos JULES itself silently ignores without rejecting configs containing members the schema does not yet cover. Pass `strict=True` to make it an error.
- **Sentinel values.** Many real-valued fields accept `-1.0` as a JULES sentinel meaning "use the default".
- **List lengths.** Fields whose length is tied to `npft`, `nnvg`, `ncpft` or `ntype` carry a `ListLen` marker and are checked by [`JulesNamelists`](../api/namelists.md), not by the per-file model.
