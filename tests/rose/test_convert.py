"""Tests for julesconf.rose.convert, the rose app to namelist conversion.

Two halves. The first is unit-level: the emission contract (ordering,
ignored settings, trailing commas, verbatim values) and environment
variable handling, all against hand-written miniatures.

The second is `TestCorpus`, which runs the ten real `rose-app.conf` files
vendored in `tests/data/rose_apps/` all the way through `f90nml` and into
`JulesNamelists`. That turns the corpus into a conformance suite for the
schemas: the apps declare `meta=jules-standalone/vn8.2` while julesconf is
pinned to vn7.9, so `KNOWN_UNKNOWN_MEMBERS` below is a live record of the
version gap.
"""

import contextlib
import re
import textwrap
import warnings
from pathlib import Path

import f90nml
import pytest

from julesconf.config import namelist_to_dict
from julesconf.rose import (
    RoseApp,
    RoseConfig,
    UnboundVariableError,
    expand_env,
    rose_app_to_namelists,
    rose_to_namelists,
)
from julesconf.schemas import (
    InactiveNamelistKeyWarning,
    JulesNamelists,
    PostponedNamelistWarning,
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
)

DATA = Path(__file__).resolve().parent.parent / "data" / "rose_apps"

APPS = [
    "eraint_rfm_2ddata",
    "gswp2_gl7",
    "gswp2_ukv",
    "imogen_layeredc",
    "loobos_crops",
    "loobos_fire",
    "loobos_irrig",
    "loobos_jules_es_1p0_biocrop_agexpand",
    "loobos_jules_es_1p0_deposition",
    "loobos_trif",
]


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
    "eraint_rfm_2ddata": 4,
    "gswp2_gl7": 4,
    "gswp2_ukv": 4,
    "imogen_layeredc": 4,
    "loobos_crops": 4,
    "loobos_fire": 4,
    "loobos_irrig": 3,
    "loobos_jules_es_1p0_biocrop_agexpand": 5,
    "loobos_jules_es_1p0_deposition": 4,
    "loobos_trif": 4,
}
"""How many distinct members of each app julesconf does not model.

The apps are vn8.2 and the schemas are vn7.9, so a non-zero count is
expected. The numbers only ever move when the schemas or the corpus do, and
moving them down is the point of the exercise.
"""

KNOWN_UNKNOWN_MEMBERS = [
    # --- post-vn7.9: present in the vn8.2 apps, absent from the vn7.9 rose
    #     metadata and from the vn7.9 user guide, so out of scope until the
    #     pin moves ---
    "JulesDrive.l_imogen",
    "JulesIrrig.irrig_option",
    "JulesSoilBiogeochem.cs_decomp_soil_moist_func",
    "JulesSoilBiogeochem.l_bgc_heat",
    # --- a whole vn7.9 namelist file julesconf deliberately does not model;
    #     ECOSSE is documented as not fully functional and users are told not
    #     to use it, so this is a scoping decision, not a gap. See AGENTS.md ---
    "JulesNamelists.jules_soil_ecosse",
]
"""Every member of the corpus that julesconf does not model, corpus-wide.

Each entry is `Model.member`. This is the schema-gap tracker: shrinking it
is the point, growing it without noticing is the risk. It stood at 97 entries
when the corpus was first vendored and fell to 4 in Phase 4.

Phase 9 took it to 75 by vendoring four more apps. That was the tracker
becoming *accurate*, not the schemas regressing: `jules_rivers_props`,
`imogen_run_list` and `imogen_anlg_vals_list` were empty blocks whose members
Phase 4 deferred purely for want of corpus traffic, and these apps supply the
traffic.

Phase 10 populated all three blocks completely (59 members), taking the
tracker to 27.

Phase 11 closed the rest of the vn7.9 member gap — all 116 remaining metadata
members across 15 blocks — taking it to 5. What is left is the four post-vn7.9
members and the one deliberately unmodelled namelist file, so every entry is
now a scoping decision rather than a backlog item.

Repeated namelist groups used to appear here as `_grp_*` pseudo-members. They
are now read as lists of blocks, one entry per occurrence — see
`REPEATED_GROUPS`.
"""

_WARNING_RE = re.compile(r"^(\w+): ignoring unknown namelist member '(\w+)'")

REPEATED_GROUPS = {
    "eraint_rfm_2ddata": {},
    "gswp2_gl7": {"output.jules_output_profile": 2},
    "gswp2_ukv": {"output.jules_output_profile": 2},
    "imogen_layeredc": {},
    "loobos_crops": {"output.jules_output_profile": 3},
    "loobos_fire": {"output.jules_output_profile": 3},
    "loobos_irrig": {"output.jules_output_profile": 3},
    "loobos_jules_es_1p0_biocrop_agexpand": {
        "output.jules_output_profile": 7,
        "prescribed_data.jules_prescribed_dataset": 4,
    },
    "loobos_jules_es_1p0_deposition": {
        "output.jules_output_profile": 7,
        "prescribed_data.jules_prescribed_dataset": 3,
    },
    "loobos_trif": {"output.jules_output_profile": 2},
}
"""Namelist groups each app repeats, and how many times.

JULES emits one `jules_output_profile` group per output profile and one
`jules_prescribed_dataset` per prescribed dataset. Most apps in the corpus
repeat at least one group, so this is the corpus's cover for the repeated-group
machinery: the counts must survive reading, validation and both TOML forms.
`eraint_rfm_2ddata` and `imogen_layeredc` repeat nothing — a single occurrence
of every group — which is the other half of the cover.

`jules_deposition_species` is deliberately absent. It repeats in no app in the
corpus -- `loobos_jules_es_1p0_deposition` has its species sections `!!`-ignored
-- so its cover is synthetic; see `tests/schemas/test_repeated_groups.py`.
"""


def group_counts(data: dict) -> dict[str, int]:
    """Count the occurrences of every repeated group in a parsed config.

    Args:
        data: A `{namelist: {block: ...}}` dict, as `read_back` returns.

    Returns:
        A `{namelist.group: occurrences}` mapping, listing only the groups
        that occur more than once.
    """
    return {
        f"{namelist}.{group}": len(blocks)
        for namelist, file_data in data.items()
        for group, blocks in file_data.items()
        if isinstance(blocks, list) and len(blocks) > 1
    }


def validated_group_counts(config: JulesNamelists) -> dict[str, int]:
    """Count the blocks of every repeated group on a validated config."""
    counts = {}
    for namelist in type(config).model_fields:
        file_model = getattr(config, namelist)
        for group in type(file_model).model_fields:
            blocks = getattr(file_model, group)
            if isinstance(blocks, list) and len(blocks) > 1:
                counts[f"{namelist}.{group}"] = len(blocks)
    return counts


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
    return {
        name.removesuffix(".nml"): namelist_to_dict(f90nml.reads(text))
        for name, text in files.items()
    }


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

    def test_validates_against_the_schemas(self, parsed):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnknownNamelistKeyWarning)
            warnings.simplefilter("ignore", InactiveNamelistKeyWarning)
            warnings.simplefilter("ignore", PostponedNamelistWarning)
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

    def test_repeated_groups_are_read_as_lists(self, app_name, parsed):
        """Every occurrence reaches the config dict, in file order."""
        assert group_counts(parsed) == REPEATED_GROUPS[app_name]

    def test_no_group_is_left_mangled(self, parsed):
        """`_grp_` keys are `f90nml`'s; none should survive the handler."""
        assert not any(
            "_grp_" in group for blocks in parsed.values() for group in blocks
        )

    def test_repeated_groups_survive_validation(self, app_name, parsed):
        """The counts read off disk are the counts the validated model holds."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config = JulesNamelists.model_validate(parsed)
        assert validated_group_counts(config) == REPEATED_GROUPS[app_name]

    def test_repeated_groups_survive_both_toml_forms(self, app_name, parsed, tmp_path):
        """A repeated group round-trips through grouped and flat TOML alike."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config = JulesNamelists.model_validate(parsed)
            for grouped in (True, False):
                path = tmp_path / f"{app_name}-{grouped}.toml"
                config.to_toml(path, grouped=grouped)
                back = JulesNamelists.from_toml(path)
        assert back.output.jules_output_profile == config.output.jules_output_profile
        assert validated_group_counts(back) == REPEATED_GROUPS[app_name]

    def test_no_repeated_group_warning_for_the_modelled_groups(self, parsed):
        """The three groups JULES repeats are modelled, so they must not warn."""
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always")
            with contextlib.suppress(ValueError):
                JulesNamelists.model_validate(parsed)
        assert not [
            entry
            for entry in record
            if issubclass(entry.category, RepeatedNamelistGroupWarning)
        ]

    def test_round_trips_through_a_directory(self, app_name, tmp_path):
        out = tmp_path / app_name
        files = rose_app_to_namelists(DATA / f"{app_name}.conf", out, env={})
        assert sorted(path.name for path in out.iterdir()) == sorted(files)
        assert (out / "timesteps.nml").read_text() == files["timesteps.nml"]
