import marimo

__generated_with = "0.23.5"
app = marimo.App(app_title="Editing namelists directly")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Editing namelists directly
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook works at julesconf's lower **container** layer: reading a JULES
    configuration directory into plain Python data, editing it, and writing it back.
    It is the layer that also carries the **input data** (driving data, initial
    conditions, tile fractions) alongside the namelists.

    This is a first-class namelist workflow, not a legacy one. If you mainly want to
    edit parameters or convert between namelists and TOML, the typed
    [`JulesNamelists`](../concepts/containers.md) model in
    [Get started](../tutorials/get-started.md) is the gentler route; come here when
    you need the raw directory data, especially input data.

    We will:

    1. Construct a `JulesConfig` object with the right paths
    2. Read an existing configuration from disk
    3. Explore the configuration data
    4. Tweak some parameters
    5. Write the modified configuration back to disk

    The example configuration we'll use is from the Loobos flux tower site, located in
    `examples/loobos/`.
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from julesconf.config import InputFilesConfig, JulesConfig

    return InputFilesConfig, JulesConfig


@app.cell
def _():
    from julesconf.schemas import JulesNamelists

    return (JulesNamelists,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Constructing a JulesConfig

    A `JulesConfig` object describes the layout of a JULES configuration directory.
    It combines two sub-configurations:

    - **`namelists`** — the directory of Fortran namelist files (all paths are fixed in advance)
    - **`inputs`** — the directory of input data files (initial conditions, tile fractions, driving data)

    The `namelists` node is already configured with default paths, so we only need to
    specify the `inputs` node at instantiation:
    """)
    return


@app.cell
def _(InputFilesConfig, JulesConfig, mo):
    jules_config = JulesConfig(
        inputs={
            "path": "inputs",
            "handler": lambda: InputFilesConfig(
                initial_conditions="initial_conditions_bb219.dat",
                tile_fractions="tile_fractions.dat",
                driving_data="Loobos_1997.dat",
            ),
        },
    )

    mo.md(f"Configured:\n\n```\n{jules_config}\n```")
    return (jules_config,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reading a configuration from disk

    Now we use our `JulesConfig` to read the entire Loobos configuration directory into a Python dict.
    """)
    return


@app.cell
def _(jules_config):
    from pathlib import Path

    loobos_dir = Path(__file__).resolve().parent / "loobos"

    config_dict = jules_config.read(loobos_dir)

    list(config_dict.keys())
    return (config_dict,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Validating the configuration

    Before exploring, validate the namelists against the JULES v7.9 Pydantic schemas.
    This catches typos, out-of-range values, and cross-namelist inconsistencies.
    """)
    return


@app.cell
def _(JulesNamelists, config_dict, mo):
    validated = JulesNamelists.model_validate(config_dict["namelists"])

    mo.md(f"Validation passed — **{type(validated).__name__}** model created")
    return (validated,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The top-level keys are `inputs` and `namelists`, matching the structure we defined.
    Let's look inside the `drive` namelist, which controls the meteorological forcing setup:
    """)
    return


@app.cell
def _(config_dict):
    config_dict["namelists"]["drive"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Exploring input data

    The `inputs` section contains the actual numerical data. Here's the tile fractions file:
    """)
    return


@app.cell
def _(config_dict):
    tile_fractions_data = config_dict["inputs"]["tile_fractions"]

    print("Comment header:")
    print(tile_fractions_data["comment"])
    print()
    print("Values (shape:", tile_fractions_data["values"].shape, "):")
    tile_fractions_data["values"]
    return


@app.cell
def _():
    import matplotlib.pyplot as plt
    import numpy as np

    return np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Plotting the driving data

    Let's verify the driving data loaded correctly by plotting a few key variables
    over the year. The Loobos 1997 dataset contains 30-minute meteorological readings.
    """)
    return


@app.cell
def _(config_dict, mo, np, plt):
    driving_data = config_dict["inputs"]["driving_data"]
    driving_values = driving_data["values"]

    num_timesteps = driving_values.shape[0]
    half_hour_intervals = np.arange(num_timesteps) / 48.0  # convert to days

    fig_101, axes_101 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axes_101[0].plot(
        half_hour_intervals, driving_values[:, 2], color="steelblue", linewidth=0.5
    )
    axes_101[0].set_ylabel("Rainfall\n(kg m⁻² s⁻¹)")
    axes_101[0].set_title("Loobos 1997 Driving Data")

    axes_101[1].plot(
        half_hour_intervals, driving_values[:, 4], color="tomato", linewidth=0.5
    )
    axes_101[1].set_ylabel("Air temp. (K)")

    axes_101[2].plot(
        half_hour_intervals, driving_values[:, 0], color="goldenrod", linewidth=0.5
    )
    axes_101[2].set_ylabel("Down SWR (W m⁻²)")
    axes_101[2].set_xlabel("Days since start of year")

    fig_101.tight_layout()
    mo.mpl.interactive(fig_101)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The seasonal patterns are clearly visible — rainfall events, temperature cycles,
    and solar radiation all look as expected for a full year of half-hourly data.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Modifying parameters

    Let's try two modifications to `timestep_len`: first an invalid value that
    breaks the schema, then a valid one.
    """)
    return


@app.cell
def _(config_dict, mo):
    original_timestep_len = config_dict["namelists"]["timesteps"]["jules_time"][
        "timestep_len"
    ]

    mo.md(f"Current `timestep_len`: **{original_timestep_len}** seconds")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Trying an invalid modification

    What happens if we set `timestep_len` to 0 seconds?
    The schema requires it to be ≥ 1, so validation will raise.
    """)
    return


@app.cell
def _(JulesNamelists, config_dict):
    config_dict["namelists"]["timesteps"]["jules_time"]["timestep_len"] = 0
    JulesNamelists.model_validate(config_dict["namelists"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Making a valid modification

    Now let's set `timestep_len` to `3600` seconds (hourly output).
    """)
    return


@app.cell
def _(config_dict):
    config_dict["namelists"]["timesteps"]["jules_time"]["timestep_len"] = 3600
    return


@app.cell
def _(JulesNamelists, config_dict, mo):
    JulesNamelists.model_validate(config_dict["namelists"])

    mo.md("Validation passed")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Writing the modified configuration to disk

    Finally, we write the updated configuration to a temporary directory.
    In practice you would use a persistent output directory.
    """)
    return


@app.cell
def _(config_dict, jules_config, mo):
    import tempfile

    with tempfile.TemporaryDirectory() as output_dir_101:
        jules_config.write(output_dir_101, config_dict)

        mo.md(
            f"Configuration written to `{output_dir_101}`\n\n"
            f"Verified: `output.nml` exists with updated `output_period = 3600`"
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Next steps

    You've now seen the core workflow:

    1. **Construct** a `JulesConfig` with paths to your namelist and input files
    2. **Read** an existing configuration directory into a Python dict
    3. **Explore** and modify the configuration data
    4. **Write** the configuration back to disk

    From here:

    - [Authoring a config in TOML](../tutorials/authoring-toml.md) — the terser form
      recommended for new projects.
    - [The containers](../concepts/containers.md) — how this layer relates to the
      typed `JulesNamelists` model.
    - [Containers & handlers reference](../api/config.md) — `JulesConfig`,
      `InputFilesConfig`, and the ASCII/NetCDF handlers in detail.
    """)
    return


if __name__ == "__main__":
    app.run()
