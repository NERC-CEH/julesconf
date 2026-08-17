# Option values (enums)

Many JULES options are choices from a fixed set — a soil hydraulic conductivity
method, a stomatal conductance model, and so on. julesconf models each as an enum,
which is how you discover what values an option will accept.

## Names and values

Each enum member has an **integer value** (what the Fortran namelist uses) and a
**name** (readable text). On input, the field accepts either — `name_or_value()`
(see [field constraints](constraints.md)) coerces a string name or its integer to
the member. On output the format decides:

- **TOML** writes the **name**: `soilhc_method = "johansen"`.
- **Namelists** write the plain **integer**: `soilhc_method = 1`.

So in a [TOML config](../../concepts/file-forms.md) you write the name, and this
page is the list of names each field accepts.

## Soil — `jules_soil.nml`

::: julesconf.schemas.jules_soil.SoilhcMethod

## Soil biogeochemistry — `jules_soil_biogeochem.nml`

::: julesconf.schemas.jules_soil_biogeochem.SoilBgcModel

::: julesconf.schemas.jules_soil_biogeochem.Ch4Substrate

## Vegetation — `jules_vegetation.nml`

::: julesconf.schemas.jules_vegetation.CanModel

::: julesconf.schemas.jules_vegetation.CanRadMod

::: julesconf.schemas.jules_vegetation.PhotoModel

::: julesconf.schemas.jules_vegetation.StomataModel

::: julesconf.schemas.jules_vegetation.IgnitionMethod

## Irrigation — `jules_irrig.nml`

::: julesconf.schemas.jules_irrig.IrrCrop

## Rivers — `jules_rivers.nml`

::: julesconf.schemas.jules_rivers.RiverRoutingAlgorithm

## Model environment — `model_environment.nml`

::: julesconf.schemas.model_environment.JulesParent

::: julesconf.schemas.model_environment.LsmId
