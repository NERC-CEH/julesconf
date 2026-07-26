"""Tests for julesconf.rose.convert, the rose app to namelist conversion.

Two halves. The first is unit-level: the emission contract (ordering,
ignored settings, trailing commas, verbatim values) and environment
variable handling, all against hand-written miniatures.

The second is `TestCorpus`, which runs the six real `rose-app.conf` files
vendored in `tests/data/rose_apps/` all the way through `f90nml` and into
`JulesNamelists`. That turns the corpus into a conformance suite for the
schemas: the apps declare `meta=jules-standalone/vn8.2` while julesconf is
pinned to vn7.9, so `KNOWN_UNKNOWN_MEMBERS` below is a live record of the
version gap.
"""

import contextlib
import json
import re
import textwrap
import warnings
from pathlib import Path

import f90nml
import pytest

from julesconf.rose import (
    RoseApp,
    RoseConfig,
    UnboundVariableError,
    expand_env,
    rose_app_to_namelists,
    rose_to_namelists,
)
from julesconf.schemas import JulesNamelists, UnknownNamelistKeyWarning

DATA = Path(__file__).resolve().parent.parent / "data" / "rose_apps"

APPS = [
    "gswp2_gl7",
    "loobos_crops",
    "loobos_fire",
    "loobos_irrig",
    "loobos_jules_es_1p0_deposition",
    "loobos_trif",
]

# Apps whose crop parameters trip a real schema bug: `jules_cropparm.delta_io`
# is typed `NonNegFloat`, but the JULES defaults for it are negative
# (-0.0507, -0.1451, ...). Being fixed in the next phase; strict xfail so the
# fix is noticed here.
CROP_DELTA_IO_APPS = ["loobos_crops", "loobos_irrig"]


def conf(text: str) -> str:
    """Dedent a triple-quoted fixture and drop its leading newline."""
    return textwrap.dedent(text).lstrip("\n")


def app(text: str) -> RoseApp:
    """Build a RoseApp from a dedented inline fixture."""
    return RoseApp.from_config(RoseConfig.parse(conf(text)))


class TestEmission:
    def test_single_group(self):
        files = rose_to_namelists(
            app("""
                [file:jules_soil.nml]
                source=namelist:jules_soil

                [namelist:jules_soil]
                dzsoil_io=0.1
            """),
            env={},
        )
        assert files == {"jules_soil.nml": "&jules_soil\ndzsoil_io=0.1,\n/\n"}

    def test_keys_are_sorted_within_a_group(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                zeta=1
                alpha=2
                mu=3
            """),
            env={},
        )
        assert files["a.nml"] == "&g\nalpha=2,\nmu=3,\nzeta=1,\n/\n"

    def test_groups_follow_source_order_not_file_order(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:zeta namelist:alpha

                [namelist:alpha]
                n=1

                [namelist:zeta]
                n=2
            """),
            env={},
        )
        assert files["a.nml"] == "&zeta\nn=2,\n/\n&alpha\nn=1,\n/\n"

    @pytest.mark.parametrize("marker", ["!", "!!"])
    def test_ignored_settings_are_skipped(self, marker):
        files = rose_to_namelists(
            app(f"""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                keep=1
                {marker}drop=2
            """),
            env={},
        )
        assert files["a.nml"] == "&g\nkeep=1,\n/\n"

    def test_ignored_section_emits_nothing(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g namelist:h

                [namelist:g]
                n=1

                [!!namelist:h]
                n=2
            """),
            env={},
        )
        assert files["a.nml"] == "&g\nn=1,\n/\n"

    def test_empty_section_still_emits_a_group(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
            """),
            env={},
        )
        assert files["a.nml"] == "&g\n/\n"

    def test_section_of_only_ignored_settings_emits_a_group(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                !!n=1
            """),
            env={},
        )
        assert files["a.nml"] == "&g\n/\n"

    def test_indexed_sections_share_a_group_name(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:p(:)

                [namelist:p(2)]
                n=2

                [namelist:p(1)]
                n=1
            """),
            env={},
        )
        assert files["a.nml"] == "&p\nn=1,\n/\n&p\nn=2,\n/\n"

    @pytest.mark.parametrize(
        "value",
        ["8*'S'", "5*1.667", "0.28e6", ".false.", "'./output'", "-0.0507,-0.1451"],
    )
    def test_values_are_copied_verbatim(self, value):
        files = rose_to_namelists(
            app(f"""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                x={value}
            """),
            env={},
        )
        assert files["a.nml"] == f"&g\nx={value},\n/\n"

    def test_multiline_value_is_kept(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                var='b','sathh',
                   ='hcon'
            """),
            env={},
        )
        assert files["a.nml"] == "&g\nvar='b','sathh',\n'hcon',\n/\n"

    def test_empty_file_declaration_yields_empty_text(self):
        assert rose_to_namelists(app("[file:a.nml]\nsource=\n"), env={}) == {
            "a.nml": ""
        }


class TestEnv:
    @pytest.mark.parametrize("spelling", ["$LOOBOS", "${LOOBOS}"])
    def test_both_spellings_substitute(self, spelling):
        assert expand_env(f"'{spelling}/data'", {"LOOBOS": "/opt"}) == "'/opt/data'"

    def test_keep_leaves_reference_verbatim(self):
        assert expand_env("$MISSING/x", {}, on_unbound="keep") == "$MISSING/x"

    def test_empty_blanks_reference(self):
        assert expand_env("$MISSING/x", {}, on_unbound="empty") == "/x"

    def test_error_raises(self):
        with pytest.raises(UnboundVariableError, match=r"\$MISSING"):
            expand_env("$MISSING/x", {}, on_unbound="error")

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="on_unbound"):
            expand_env("x", {}, on_unbound="nonsense")  # type: ignore[arg-type]

    def test_escaped_reference_is_left_alone(self):
        assert expand_env(r"\$KEEP", {"KEEP": "no"}) == "$KEEP"

    def test_double_escape_still_substitutes(self):
        assert expand_env(r"\\$X", {"X": "y"}) == "\\y"

    def test_multiple_references_in_one_value(self):
        env = {"A": "1", "B": "2"}
        assert expand_env("$A/${B}/$A", env) == "1/2/1"

    def test_substitutions_are_reported(self):
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                x='$HERE/$THERE'
            """),
            env={"HERE": "/opt"},
        )
        assert files["a.nml"] == "&g\nx='/opt/$THERE',\n/\n"
        assert files.substituted == {"HERE": "/opt"}
        assert files.unresolved == {"THERE"}

    def test_error_mode_propagates_through_conversion(self):
        with pytest.raises(UnboundVariableError):
            rose_to_namelists(
                app("""
                    [file:a.nml]
                    source=namelist:g

                    [namelist:g]
                    x=$NOPE
                """),
                env={},
                on_unbound="error",
            )

    def test_env_defaults_to_os_environ(self, monkeypatch):
        monkeypatch.setenv("JULESCONF_TEST_VAR", "/tmp/xyz")
        files = rose_to_namelists(
            app("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                x=$JULESCONF_TEST_VAR
            """)
        )
        assert files["a.nml"] == "&g\nx=/tmp/xyz,\n/\n"


class TestWriteToDirectory:
    @pytest.fixture
    def conf_path(self, tmp_path) -> Path:
        path = tmp_path / "rose-app.conf"
        path.write_text(
            conf("""
                [file:a.nml]
                source=namelist:g

                [namelist:g]
                n=1
            """)
        )
        return path

    def test_writes_files(self, conf_path, tmp_path):
        out = tmp_path / "namelists"
        rose_app_to_namelists(conf_path, out, env={})
        assert (out / "a.nml").read_text() == "&g\nn=1,\n/\n"

    def test_refuses_to_overwrite_by_default(self, conf_path, tmp_path):
        out = tmp_path / "namelists"
        rose_app_to_namelists(conf_path, out, env={})
        with pytest.raises(FileExistsError):
            rose_app_to_namelists(conf_path, out, env={})

    def test_overwrite_ok(self, conf_path, tmp_path):
        out = tmp_path / "namelists"
        rose_app_to_namelists(conf_path, out, env={})
        rose_app_to_namelists(conf_path, out, env={}, overwrite_ok=True)
        assert (out / "a.nml").read_text() == "&g\nn=1,\n/\n"


# ---------------------------------------------------------------------------
# The vendored corpus
# ---------------------------------------------------------------------------

EXPECTED_FILE_COUNT = 35
"""Every JULES rose app declares the same 35 output files.

That is six more than the 29 julesconf models: the postponed `cable_*`,
`oasis_rivers` and `red_params` namelists each get their own file.
"""

UNKNOWN_MEMBER_COUNTS = {
    "gswp2_gl7": 31,
    "loobos_crops": 31,
    "loobos_fire": 63,
    "loobos_irrig": 33,
    "loobos_jules_es_1p0_deposition": 55,
    "loobos_trif": 38,
}
"""How many distinct members of each app julesconf does not model.

The apps are vn8.2 and the schemas are vn7.9, so a non-zero count is
expected. The numbers only ever move when the schemas or the corpus do, and
moving them down is the point of the exercise.
"""

KNOWN_UNKNOWN_MEMBERS = [
    # --- fire: the whole vn8.2 fire index switch set ---
    "FireSwitches.canadian_flag",
    "FireSwitches.canadian_hemi_opt",
    "FireSwitches.mcarthur_flag",
    "FireSwitches.mcarthur_opt",
    "FireSwitches.nesterov_flag",
    # --- agriculture / land use ---
    "JulesAgric.frac_agr",
    "JulesAgric.frac_past",
    "JulesAgric.read_from_dump",
    "JulesAgric.zero_agric",
    "JulesAgric.zero_past",
    "JulesCo2.read_from_dump",
    # --- crops ---
    "JulesCropparm.initial_c_dvi_io",
    "JulesCropparm.initial_carbon_io",
    "JulesCropparm.mu_io",
    "JulesCropparm.sen_dvi_io",
    "JulesCropparm.t_mort_io",
    "JulesCropparm.yield_frac_io",
    # --- ancillaries and the grid ---
    "JulesFrac.frac_name",
    "JulesInputGrid.grid_dim_name",
    "JulesInputGrid.npoints",
    "JulesLandFrac.file",
    "JulesLandFrac.land_frac_name",
    "JulesLatlon.read_from_dump",
    "JulesLatlon.tpl_name",
    "JulesModelGrid.land_only",
    "JulesModelGrid.use_subgrid",
    "JulesNlsizes.bl_levels",
    "JulesSoilProps.read_list",
    "JulesSoilProps.tpl_name",
    "JulesSurfHgt.zero_height",
    # --- irrigation ---
    "JulesIrrig.irrig_option",
    "JulesIrrigProps.const_frac_irr",
    "JulesIrrigProps.const_irrfrac_irrtiles",
    "JulesIrrigProps.read_file",
    # --- BVOC emissions and fire-emission factors on the PFTs ---
    "JulesPftparm.aef_io",
    "JulesPftparm.avg_ba_io",
    "JulesPftparm.ccleaf_max_io",
    "JulesPftparm.ccleaf_min_io",
    "JulesPftparm.ccwood_max_io",
    "JulesPftparm.ccwood_min_io",
    "JulesPftparm.ci_st_io",
    "JulesPftparm.fef_bc_io",
    "JulesPftparm.fef_c2h4_io",
    "JulesPftparm.fef_c2h6_io",
    "JulesPftparm.fef_c3h8_io",
    "JulesPftparm.fef_ch4_io",
    "JulesPftparm.fef_co2_io",
    "JulesPftparm.fef_co_io",
    "JulesPftparm.fef_dms_io",
    "JulesPftparm.fef_hcho_io",
    "JulesPftparm.fef_mecho_io",
    "JulesPftparm.fef_nh3_io",
    "JulesPftparm.fef_nox_io",
    "JulesPftparm.fef_oc_io",
    "JulesPftparm.fef_so2_io",
    "JulesPftparm.gpp_st_io",
    "JulesPftparm.ief_io",
    "JulesPftparm.mef_io",
    "JulesPftparm.tef_io",
    # --- misc switches ---
    "JulesPrntControl.prnt_writers",
    "JulesSoilBiogeochem.cs_decomp_soil_moist_func",
    "JulesSoilBiogeochem.l_bgc_heat",
    "JulesTriffid.dpm_rpm_ratio_io",
    "JulesTriffid.retran_l_io",
    "JulesTriffid.retran_r_io",
    "JulesVegetation.frac_min",
    "JulesVegetation.frac_seed",
    "JulesVegetation.l_bvoc_emis",
    "JulesVegetation.l_gleaf_fix",
    "JulesVegetation.l_ht_compete",
    "JulesVegetation.l_landuse",
    "JulesVegetation.l_leaf_n_resp_fix",
    "JulesVegetation.l_limit_canhc",
    "JulesVegetation.l_o3_damage",
    "JulesVegetation.l_prescsow",
    "JulesVegetation.l_red",
    "JulesVegetation.l_scale_resp_pm",
    "JulesVegetation.l_spec_veg_z0",
    "JulesVegetation.l_stem_resp_fix",
    "JulesVegetation.l_sugar",
    "JulesVegetation.l_trif_biocrop",
    "JulesVegetation.l_trif_crop",
    "JulesVegetation.l_use_pft_psi",
    "JulesVegetation.l_vegdrag_pft",
    "JulesVegetation.phenol_period",
    "JulesVegetation.pow",
    # --- the ECOSSE soil scheme, absent from JulesNamelists entirely ---
    "JulesNamelists.jules_soil_ecosse",
    # --- repeated groups: julesconf models one profile / dataset per file,
    #     real apps declare several, and f90nml renames the duplicates ---
    "OutputNamelist._grp_jules_output_profile_0",
    "OutputNamelist._grp_jules_output_profile_1",
    "OutputNamelist._grp_jules_output_profile_2",
    "OutputNamelist._grp_jules_output_profile_3",
    "OutputNamelist._grp_jules_output_profile_4",
    "OutputNamelist._grp_jules_output_profile_5",
    "OutputNamelist._grp_jules_output_profile_6",
    "PrescribedDataNamelist._grp_jules_prescribed_dataset_0",
    "PrescribedDataNamelist._grp_jules_prescribed_dataset_1",
    "PrescribedDataNamelist._grp_jules_prescribed_dataset_2",
]
"""Every member of the corpus that julesconf does not model, corpus-wide.

Each entry is `Model.member`. This is the schema-gap tracker: shrinking it
is the point, growing it without noticing is the risk.
"""

_WARNING_RE = re.compile(r"^(\w+): ignoring unknown namelist member '(\w+)'")


def unknown_members(data: dict) -> set[str]:
    """Validate a config dict and collect the members julesconf ignored.

    Validation failures are swallowed: an invalid config still emits every
    unknown-key warning, and whether it validates is tested separately.

    Args:
        data: A `{namelist: {block: {member: value}}}` dict.

    Returns:
        The unknown members, each as a `Model.member` string.
    """
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        with contextlib.suppress(ValueError):
            JulesNamelists.model_validate(data)

    found = set()
    for entry in record:
        if not issubclass(entry.category, UnknownNamelistKeyWarning):
            continue
        match = _WARNING_RE.match(str(entry.message))
        assert match is not None, entry.message
        found.add(f"{match[1]}.{match[2]}")
    return found


@pytest.fixture(scope="module", params=APPS)
def app_name(request) -> str:
    """The stem of each vendored app, parametrised."""
    return request.param


@pytest.fixture(scope="module")
def converted(app_name) -> dict[str, str]:
    """The app converted to `{filename: namelist text}`.

    Converted with an empty environment, so every `$VAR` in the corpus is
    unresolved and left verbatim — the apps are only meaningful inside a
    cylc workflow, and none of the paths are read here anyway.
    """
    return rose_to_namelists(RoseApp.parse_file(DATA / f"{app_name}.conf"), env={})


def read_back(files: dict[str, str]) -> dict:
    """Read converted namelist text back through f90nml.

    Args:
        files: A `{filename: namelist text}` mapping.

    Returns:
        A `{namelist: {block: {member: value}}}` dict of plain JSON types,
        keyed without the `.nml` suffix, ready for `model_validate`.
    """
    data = {
        name.removesuffix(".nml"): f90nml.reads(text).todict()
        for name, text in files.items()
    }
    return json.loads(json.dumps(data))


@pytest.fixture(scope="module")
def parsed(converted) -> dict:
    """The converted files read back through f90nml, keyed without `.nml`."""
    return read_back(converted)


class TestCorpus:
    def test_all_apps_are_vendored(self):
        assert sorted(path.stem for path in DATA.glob("*.conf")) == APPS

    def test_declared_meta_is_vn8_2(self, app_name):
        app = RoseApp.parse_file(DATA / f"{app_name}.conf")
        assert app.meta == "jules-standalone/vn8.2"

    def test_produces_the_expected_files(self, converted):
        assert len(converted) == EXPECTED_FILE_COUNT
        assert all(name.endswith(".nml") for name in converted)

    def test_covers_every_namelist_julesconf_models(self, converted):
        from julesconf.config import NamelistConfig

        required = {
            node.path.name  # type: ignore[union-attr]
            for node in NamelistConfig().__dict__.values()
        }
        assert required <= set(converted)

    def test_f90nml_parses_every_file(self, parsed):
        assert all(isinstance(blocks, dict) for blocks in parsed.values())

    def test_unresolved_variables_are_kept_verbatim(self, converted):
        assert "$" in "".join(converted.values())

    @pytest.mark.parametrize(
        "app_name",
        [
            pytest.param(
                name,
                marks=pytest.mark.xfail(
                    strict=True,
                    reason=(
                        "jules_cropparm.delta_io is typed NonNegFloat but the "
                        "JULES defaults are negative; schema bug, fixed next phase"
                    ),
                ),
            )
            if name in CROP_DELTA_IO_APPS
            else name
            for name in APPS
        ],
        indirect=True,
    )
    def test_validates_against_the_schemas(self, parsed):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnknownNamelistKeyWarning)
            JulesNamelists.model_validate(parsed)

    def test_unknown_members_are_the_known_set(self, app_name, parsed):
        found = unknown_members(parsed)
        assert found <= set(KNOWN_UNKNOWN_MEMBERS)
        assert len(found) == UNKNOWN_MEMBER_COUNTS[app_name]

    def test_every_known_unknown_is_still_reachable(self):
        """The tracker must not accumulate entries the corpus no longer hits."""
        seen = set()
        for name in APPS:
            files = rose_to_namelists(RoseApp.parse_file(DATA / f"{name}.conf"), env={})
            seen |= unknown_members(read_back(files))
        assert seen == set(KNOWN_UNKNOWN_MEMBERS)

    def test_round_trips_through_a_directory(self, app_name, tmp_path):
        out = tmp_path / app_name
        files = rose_app_to_namelists(DATA / f"{app_name}.conf", out, env={})
        assert sorted(path.name for path in out.iterdir()) == sorted(files)
        assert (out / "timesteps.nml").read_text() == files["timesteps.nml"]
