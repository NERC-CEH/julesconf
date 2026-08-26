# Option values (enums)

Many JULES options are choices from a fixed set — a soil hydraulic conductivity method, a stomatal conductance model, and so on.
julesconf models each as an enum, which is how you discover what values an option will accept.

## Names and values

Each enum member has an **integer value** (what the Fortran namelist uses) and a **name** (readable text).
On input, the field accepts either — `name_or_value()` (see [field constraints](api/constraints.md)) coerces a string name or its integer to the member.
On output the format decides:

- **TOML** writes the **name**: `soilhc_method = "johansen"`.
- **Namelists** write the plain **integer**: `soilhc_method = 1`.

So in a [TOML config](../guide/toml.md#the-two-forms) you write the name, and this page is the list of names each field accepts.

## Driving data — `drive.nml`

::: julesconf.schemas.drive.PrecipDisaggMethod

## Radiation — `jules_radiation.nml`

::: julesconf.schemas.jules_radiation.SeaAlbedoMethod

## Surface — `jules_surface.nml`

::: julesconf.schemas.jules_surface.FormDrag

::: julesconf.schemas.jules_surface.FdHillOption

::: julesconf.schemas.jules_surface.FdStabilityDep

::: julesconf.schemas.jules_surface.IModiscOpt

::: julesconf.schemas.jules_surface.SrfExCnvGust

::: julesconf.schemas.jules_surface.AllTiles

::: julesconf.schemas.jules_surface.MoIterCorrection

::: julesconf.schemas.jules_surface.AggregateOpt

::: julesconf.schemas.jules_surface.ScreenDiagMethod

::: julesconf.schemas.jules_surface.AnthropHeatOption

## Snow — `jules_snow.nml`

::: julesconf.schemas.jules_snow.FracSnowSublMelt

::: julesconf.schemas.jules_snow.GraupelOptions

::: julesconf.schemas.jules_snow.SnowCondParm

::: julesconf.schemas.jules_snow.GrainGrowthOpt

::: julesconf.schemas.jules_snow.RelayerOpt

::: julesconf.schemas.jules_snow.BasalMeltingOpt

## Soil — `jules_soil.nml`

::: julesconf.schemas.jules_soil.SoilhcMethod

## Soil biogeochemistry — `jules_soil_biogeochem.nml`

::: julesconf.schemas.jules_soil_biogeochem.SoilBgcModel

::: julesconf.schemas.jules_soil_biogeochem.Ch4Substrate

## Vegetation — `jules_vegetation.nml`

::: julesconf.schemas.jules_vegetation.CanModel

::: julesconf.schemas.jules_vegetation.PhotoAcclimModel

::: julesconf.schemas.jules_vegetation.PhotoActModel

::: julesconf.schemas.jules_vegetation.PhotoJvModel

::: julesconf.schemas.jules_vegetation.CanRadMod

::: julesconf.schemas.jules_vegetation.PhotoModel

::: julesconf.schemas.jules_vegetation.StomataModel

::: julesconf.schemas.jules_vegetation.IgnitionMethod

::: julesconf.schemas.jules_vegetation.FsmcShape

## Irrigation — `jules_irrig.nml`

::: julesconf.schemas.jules_irrig.IrrCrop

## Rivers — `jules_rivers.nml`

::: julesconf.schemas.jules_rivers.RiverRoutingAlgorithm

::: julesconf.schemas.jules_rivers.LakeWaterConserveMethod

::: julesconf.schemas.jules_rivers.TripGlobeShape

::: julesconf.schemas.jules_rivers.OverbankModel

## Water resources — `jules_water_resources.nml`

::: julesconf.schemas.jules_water_resources.NrGwaterModel

## Science fixes — `science_fixes.nml`

::: julesconf.schemas.science_fixes.CtileOrogFix

## Output — `output.nml`

::: julesconf.schemas.output.FilePeriod

## Model environment — `model_environment.nml`

::: julesconf.schemas.model_environment.JulesParent

::: julesconf.schemas.model_environment.LsmId

## Deposition — `jules_deposition.nml`

::: julesconf.schemas.jules_deposition.DryDepModel

::: julesconf.schemas.jules_deposition.DepH2SoilScheme

## Fire — `fire.nml`

::: julesconf.schemas.fire.McArthurOpt

## IMOGEN — `imogen.nml`

::: julesconf.schemas.imogen.ChangeMetdataMethod

## Print control — `jules_prnt_control.nml`

::: julesconf.schemas.jules_prnt_control.PrntWriters
