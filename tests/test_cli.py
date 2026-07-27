"""Tests for the `julesconf` command-line interface and its error formatter.

The formatter in `julesconf._errors` is deliberately exercised twice: directly,
against a `ValidationError` built from a synthetic config, and through the CLI,
so that a change to either half cannot quietly break the other.

Every CLI test chdirs into `tmp_path` — the file handlers filter absolute
paths, so a namelists directory has to be reached by a relative path.
"""

import re
import warnings
from pathlib import Path

import pytest
from conftest import minimal_valid
from pydantic import ValidationError
from typer.testing import CliRunner

from julesconf._errors import (
    WARNING_KINDS,
    ConfigError,
    WarningGroup,
    WarningKind,
    format_config_errors,
    format_validation_error,
    format_warnings,
    group_warnings,
    iter_config_errors,
)
from julesconf.cli import app
from julesconf.rose import rose_app_to_namelists
from julesconf.schemas import (
    JulesNamelists,
    RepeatedNamelistGroupWarning,
    UnknownNamelistKeyWarning,
)

DATA = Path(__file__).resolve().parent / "data" / "rose_apps"
CORPUS = "loobos_fire"

runner = CliRunner()


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """Run the test from inside `tmp_path`; handlers reject absolute paths."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def namelists(cwd):
    """A valid namelists directory, converted from a corpus rose app."""
    destination = cwd / "nml"
    rose_app_to_namelists(DATA / f"{CORPUS}.conf", destination)
    return Path("nml")


@pytest.fixture
def config_toml(cwd, namelists):
    """A valid grouped TOML config, written from the corpus app."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        JulesNamelists.from_namelists(namelists).to_toml(cwd / "config.toml")
    return Path("config.toml")


def invalid_config() -> dict:
    """A config with one failure of each shape the formatter has to handle."""
    data = minimal_valid()
    data["jules_vegetation"]["jules_vegetation"]["can_rad_mod"] = 7
    data["jules_soil"]["jules_soil"]["sm_levels"] = 4
    data["jules_soil"]["jules_soil"]["dzsoil_io"] = [0.1, 0.25, 0.65]
    data["jules_soil_biogeochem"] = {"jules_soil_biogeochem": {"soil_bgc_model": "x"}}
    data["pft_params"]["jules_pftparm"]["albsnc_max_io"] = [0.1, "not a number"]
    return data


def validation_error() -> ValidationError:
    """Validate `invalid_config` and return the resulting error."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ValidationError) as excinfo:
            JulesNamelists.model_validate(invalid_config())
    return excinfo.value


def break_namelist(directory: Path) -> None:
    """Introduce three validation failures into a namelists directory."""
    substitutions = {
        "jules_vegetation.nml": (r"can_rad_mod=\d+,", "can_rad_mod=7,"),
        "jules_soil.nml": (r"dzsoil_io=[^\n]*", "dzsoil_io=0.1,0.25,0.65,"),
        "jules_soil_biogeochem.nml": (
            r"soil_bgc_model=[^\n]*",
            "soil_bgc_model='roth_c',",
        ),
    }
    for name, (pattern, replacement) in substitutions.items():
        path = directory / name
        path.write_text(re.sub(pattern, replacement, path.read_text()))


# ----------------------------------------------------------------------
# The error formatter, on its own
# ----------------------------------------------------------------------


class TestErrorFormatter:
    def test_locations_are_namelist_block_member(self):
        errors = {error.location for error in iter_config_errors(validation_error())}
        assert "jules_vegetation.nml  JULES_VEGETATION  can_rad_mod" in errors
        assert (
            "jules_soil_biogeochem.nml  JULES_SOIL_BIOGEOCHEM  soil_bgc_model" in errors
        )

    def test_block_name_is_upper_cased(self):
        error = next(iter_config_errors(validation_error()))
        assert error.block is not None
        assert error.block.isupper()

    def test_namelist_gains_the_nml_suffix(self):
        for error in iter_config_errors(validation_error()):
            assert error.namelist is None or error.namelist.endswith(".nml")

    def test_list_index_is_appended_to_the_member(self):
        members = {error.member for error in iter_config_errors(validation_error())}
        assert "albsnc_max_io[1]" in members

    def test_block_level_error_recovers_the_member_from_its_message(self):
        # The `dzsoil_io` length check is attached to JULES_SOIL, so pydantic
        # reports a two-element location; the member comes from the message.
        errors = {
            error.location: error.message
            for error in iter_config_errors(validation_error())
        }
        location = "jules_soil.nml  JULES_SOIL  dzsoil_io"
        assert location in errors
        assert errors[location] == "dzsoil_io has 3 element(s), expected sm_levels=4"

    def test_enum_error_names_the_value_and_the_valid_ones(self):
        messages = {error.message for error in iter_config_errors(validation_error())}
        assert "7 is not a valid value; valid values: 1, 2, 3, 4, 5, 6" in messages

    def test_enum_name_error_lists_the_valid_names(self):
        messages = " ".join(
            error.message for error in iter_config_errors(validation_error())
        )
        assert "is not a valid name; valid names:" in messages
        assert "single_pool" in messages

    def test_pydantic_framing_is_stripped(self):
        for error in iter_config_errors(validation_error()):
            assert not error.message.startswith("Value error, ")

    def test_cross_namelist_error_has_no_location(self):
        data = minimal_valid()
        data["jules_vegetation"]["jules_vegetation"]["l_triffid"] = True
        data["jules_soil_biogeochem"] = {
            "jules_soil_biogeochem": {"soil_bgc_model": "single_pool"}
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationError) as excinfo:
                JulesNamelists.model_validate(data)

        (error,) = iter_config_errors(excinfo.value)
        assert error.namelist is None
        assert error.location == "<cross-namelist>"
        assert error.message == "Can't use 1-pool with TRIFFID"

    def test_report_is_headed_by_the_count(self):
        report = format_validation_error(validation_error())
        assert report.startswith("Validation failed (4 errors):")

    def test_report_singular_for_one_error(self):
        report = format_config_errors(
            [ConfigError("a.nml", "A", "b", "something is wrong")]
        )
        assert report.startswith("Validation failed (1 error):")
        assert "  a.nml  A  b\n    something is wrong\n" in report

    def test_long_messages_are_wrapped_not_left_to_the_terminal(self):
        report = format_config_errors([ConfigError("a.nml", "A", "b", "word " * 60)])
        assert all(len(line) <= 79 for line in report.splitlines())

    def test_non_mapping_input_is_located_at_the_block(self):
        # A block whose value is not a table at all: there is no member dict to
        # recover a name from, so the error stops at the block.
        data = minimal_valid()
        data["jules_soil"]["jules_soil"] = "not a table"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationError) as excinfo:
                JulesNamelists.model_validate(data)

        located = [
            error
            for error in iter_config_errors(excinfo.value)
            if error.namelist == "jules_soil.nml"
        ]
        assert located
        assert all(error.member is None for error in located)

    def test_repeated_group_index_is_shown_on_the_block_one_based(self):
        """A failure in the third profile must say which profile it was.

        Pydantic locates it `('output', 'jules_output_profile', 2, ...)`; the
        index belongs to the group, and is displayed the way JULES and rose
        number the occurrences -- from 1.
        """
        data = minimal_valid()
        data["output"] = {
            "jules_output": {"nprofiles": 3},
            "jules_output_profile": [{}, {}, {"file_period": 5}],
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationError) as excinfo:
                JulesNamelists.model_validate(data)

        (error,) = iter_config_errors(excinfo.value)
        assert error.namelist == "output.nml"
        assert error.block == "JULES_OUTPUT_PROFILE[3]"
        assert error.member == "file_period"
        assert error.location == "output.nml  JULES_OUTPUT_PROFILE[3]  file_period"

    def test_a_whole_config_check_names_the_occurrence_in_its_message(self):
        """The `ListLen` walk runs on `JulesNamelists`, so the path is the message.

        It still has to say *which* profile, and it numbers them from 1, as the
        block index does.
        """
        data = minimal_valid()
        data["output"] = {
            "jules_output": {"nprofiles": 2},
            "jules_output_profile": [{}, {"nvars": 1, "var": ["a", "b"]}],
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationError) as excinfo:
                JulesNamelists.model_validate(data)

        (error,) = iter_config_errors(excinfo.value)
        assert error.location == "<cross-namelist>"
        assert error.message.startswith("output.jules_output_profile(2).var has 2")

    def test_str_of_a_config_error(self):
        error = ConfigError("a.nml", "A", "b", "boom")
        assert str(error) == "a.nml  A  b\n  boom"


class TestWarningReport:
    def raised(self) -> list[warnings.WarningMessage]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warnings.warn("first", UnknownNamelistKeyWarning, stacklevel=1)
            warnings.warn("first", UnknownNamelistKeyWarning, stacklevel=1)
            warnings.warn("second", UnknownNamelistKeyWarning, stacklevel=1)
            warnings.warn("dropped", RepeatedNamelistGroupWarning, stacklevel=1)
        return list(caught)

    def test_every_julesconf_warning_has_presentation_metadata(self):
        assert set(WARNING_KINDS) == {
            "UnknownNamelistKeyWarning",
            "PostponedNamelistWarning",
            "RepeatedNamelistGroupWarning",
            "InactiveNamelistKeyWarning",
        }

    def test_counts_include_duplicates_but_messages_do_not(self):
        groups = {group.category: group for group in group_warnings(self.raised())}
        unknown = groups["UnknownNamelistKeyWarning"]
        assert unknown.count == 3
        assert unknown.messages == ["first", "second"]

    def test_repeated_groups_are_reported_first(self):
        groups = group_warnings(self.raised())
        assert groups[0].category == "RepeatedNamelistGroupWarning"

    def test_advisory_categories_sort_after_data_loss(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for _ in range(9):
                warnings.warn("noise", UserWarning, stacklevel=1)
            warnings.warn("dropped", RepeatedNamelistGroupWarning, stacklevel=1)
        labels = [group.kind.label for group in group_warnings(list(caught))]
        assert labels == ["data loss", "advisory"]

    def test_report_names_the_severity_band(self):
        report = format_warnings(group_warnings(self.raised()))
        assert report.startswith("4 warnings:")
        assert "RepeatedNamelistGroupWarning (1) -- data loss" in report
        assert "UnknownNamelistKeyWarning (3) -- data loss" in report

    def test_report_truncates_a_long_message_list(self):
        group = WarningGroup(
            category="UnknownNamelistKeyWarning",
            kind=WARNING_KINDS["UnknownNamelistKeyWarning"],
            messages=[f"member {i}" for i in range(9)],
            count=9,
        )
        report = format_warnings([group], max_messages=3)
        assert "... and 6 more" in report

    def test_empty_report_is_empty(self):
        assert format_warnings([]) == ""

    def test_kind_without_explanation_still_renders(self):
        group = WarningGroup("X", WarningKind("advisory", ""), ["m"], 1)
        assert "X (1) -- advisory" in format_warnings([group])


# ----------------------------------------------------------------------
# The commands
# ----------------------------------------------------------------------


class TestVersion:
    def test_version_prints_and_exits_zero(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("julesconf ")

    def test_bare_invocation_shows_help(self):
        result = runner.invoke(app, [])
        assert "validate" in result.output
        assert "convert" in result.output


class TestValidate:
    def test_namelists_directory(self, namelists):
        result = runner.invoke(app, ["validate", str(namelists)])
        assert result.exit_code == 0
        assert "is valid" in result.output

    def test_toml_file(self, config_toml):
        result = runner.invoke(app, ["validate", str(config_toml)])
        assert result.exit_code == 0
        assert "is valid" in result.output

    def test_quiet_drops_the_success_line(self, namelists):
        result = runner.invoke(app, ["validate", str(namelists), "-q"])
        assert result.exit_code == 0
        assert "is valid" not in result.output

    def test_warnings_are_grouped_and_labelled(self, namelists):
        result = runner.invoke(app, ["validate", str(namelists)])
        assert "UnknownNamelistKeyWarning" in result.output
        assert "data loss" in result.output
        assert "PostponedNamelistWarning" in result.output

    def test_a_corpus_app_no_longer_reports_repeated_groups(self, namelists):
        """`loobos_fire` has three output profiles, and all three are modelled."""
        result = runner.invoke(app, ["validate", str(namelists)])
        assert "RepeatedNamelistGroupWarning" not in result.output

    def test_invalid_config_exits_one_and_locates_each_error(self, cwd, namelists):
        break_namelist(cwd / namelists)
        result = runner.invoke(app, ["validate", str(namelists)])
        assert result.exit_code == 1
        assert "Validation failed (3 errors):" in result.output
        assert "jules_vegetation.nml  JULES_VEGETATION  can_rad_mod" in result.output
        assert "jules_soil.nml  JULES_SOIL  dzsoil_io" in result.output
        assert (
            "jules_soil_biogeochem.nml  JULES_SOIL_BIOGEOCHEM  soil_bgc_model"
            in result.output
        )

    def test_strict_escalates_warnings_to_a_failure(self, namelists):
        assert runner.invoke(app, ["validate", str(namelists)]).exit_code == 0
        result = runner.invoke(app, ["validate", str(namelists), "--strict"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_missing_path_is_a_usage_error(self, cwd):
        result = runner.invoke(app, ["validate", "nowhere"])
        assert result.exit_code == 2

    def test_a_file_that_is_neither_form_is_a_usage_error(self, cwd):
        (cwd / "notes.txt").write_text("not a config")
        result = runner.invoke(app, ["validate", "notes.txt"])
        assert result.exit_code == 2
        assert "neither a namelists directory nor a .toml file" in result.output

    def test_malformed_toml_exits_one(self, cwd):
        (cwd / "broken.toml").write_text("this is not = = toml\n")
        result = runner.invoke(app, ["validate", "broken.toml"])
        assert result.exit_code == 1
        assert "Error:" in result.output


class TestValidateSingleNamelist:
    def test_one_file_is_valid(self, cwd, namelists):
        result = runner.invoke(app, ["validate", str(namelists / "jules_soil.nml")])
        assert result.exit_code == 0
        assert "is valid on its own" in result.output

    def test_says_the_cross_namelist_checks_were_skipped(self, cwd, namelists):
        result = runner.invoke(app, ["validate", str(namelists / "jules_soil.nml")])
        assert "<cross-namelist> rules were skipped" in result.output
        assert "does not mean the configuration is valid" in result.output

    def test_the_caveat_survives_quiet(self, cwd, namelists):
        """`--quiet` drops noise, not the statement of what was not checked."""
        result = runner.invoke(
            app, ["validate", str(namelists / "jules_soil.nml"), "-q"]
        )
        assert result.exit_code == 0
        assert "is valid on its own" not in result.output
        assert "<cross-namelist> rules were skipped" in result.output

    def test_invalid_file_exits_one_and_locates_the_error(self, cwd, namelists):
        break_namelist(cwd / namelists)
        result = runner.invoke(app, ["validate", str(namelists / "jules_soil.nml")])
        assert result.exit_code == 1
        assert "Validation failed (1 error):" in result.output
        assert "jules_soil.nml  JULES_SOIL  dzsoil_io" in result.output

    def test_a_failure_within_the_file_is_still_reported(self, cwd, namelists):
        """Only the *cross*-namelist rules are skipped, not the block's own."""
        break_namelist(cwd / namelists)
        result = runner.invoke(
            app, ["validate", str(namelists / "jules_soil_biogeochem.nml")]
        )
        assert result.exit_code == 1
        assert "soil_bgc_model" in result.output

    def test_a_cross_namelist_failure_is_not_reported(self, cwd, namelists):
        """A file whose only problem lies in another namelist passes alone.

        `l_triffid` with the single-pool soil carbon model is rejected by the
        whole-directory read, as `<cross-namelist>`. Reading `jules_vegetation`
        on its own cannot see the soil model, which is exactly what the
        skipped-checks notice warns about.
        """
        veg = namelists / "jules_vegetation.nml"
        (cwd / veg).write_text(
            re.sub(r"l_triffid=[^\n]*", "l_triffid=.true.,", (cwd / veg).read_text())
        )
        bgc = namelists / "jules_soil_biogeochem.nml"
        (cwd / bgc).write_text(
            re.sub(
                r"soil_bgc_model=[^\n]*",
                "soil_bgc_model='single_pool',",
                (cwd / bgc).read_text(),
            )
        )
        assert runner.invoke(app, ["validate", str(veg), "-q"]).exit_code == 0
        assert runner.invoke(app, ["validate", str(bgc), "-q"]).exit_code == 0
        result = runner.invoke(app, ["validate", str(namelists), "-q"])
        assert result.exit_code == 1
        assert "<cross-namelist>" in result.output

    def test_length_check_is_skipped_not_run(self, cwd, namelists):
        """`dzsoil_io` is checked against `sm_levels`, a sibling in the file.

        The `npft`-length arrays are the ones that cannot be checked, since
        `npft` lives in another file. Truncating one must therefore pass here
        and fail on the directory.
        """
        path = cwd / namelists / "pft_params.nml"
        path.write_text(
            re.sub(r"canht_ft_io=[^\n]*", "canht_ft_io=19.01,", path.read_text())
        )
        assert (
            runner.invoke(app, ["validate", "nml/pft_params.nml", "-q"]).exit_code == 0
        )
        assert runner.invoke(app, ["validate", str(namelists), "-q"]).exit_code == 1

    def test_strict_escalates_warnings_to_a_failure(self, cwd, namelists):
        path = cwd / namelists / "jules_soil.nml"
        path.write_text(
            path.read_text().replace("&jules_soil", "&jules_soil\n nonsense=1,")
        )
        assert (
            runner.invoke(
                app, ["validate", str(namelists / "jules_soil.nml")]
            ).exit_code
            == 0
        )
        result = runner.invoke(
            app, ["validate", str(namelists / "jules_soil.nml"), "--strict"]
        )
        assert result.exit_code == 1
        assert "UnknownNamelistKeyWarning" in result.output

    def test_a_postponed_namelist_is_a_usage_error(self, cwd, namelists):
        (cwd / namelists / "cable_pfts.nml").write_text("&cable_pfts\n/\n")
        result = runner.invoke(app, ["validate", "nml/cable_pfts.nml"])
        assert result.exit_code == 2
        assert "deliberately does not model" in result.output

    def test_an_unknown_namelist_name_is_a_usage_error(self, cwd, namelists):
        (cwd / namelists / "notes.nml").write_text("&notes\n/\n")
        result = runner.invoke(app, ["validate", "nml/notes.nml"])
        assert result.exit_code == 2
        assert "is not a JULES namelist file julesconf models" in result.output


class TestFormat:
    def formatted(self, cwd, *args: str) -> bytes:
        result = runner.invoke(app, ["format", *args])
        assert result.exit_code == 0, result.output
        return (cwd / "config.toml").read_bytes()

    def test_in_place_is_idempotent(self, cwd, config_toml):
        once = self.formatted(cwd, str(config_toml), "--in-place", "-q")
        twice = self.formatted(cwd, str(config_toml), "--in-place", "-q")
        assert once == twice

    def test_flat_form_is_idempotent(self, cwd, config_toml):
        once = self.formatted(cwd, str(config_toml), "-i", "--flat", "-q")
        twice = self.formatted(cwd, str(config_toml), "-i", "--flat", "-q")
        assert once == twice
        assert b"[[pft]]" not in once

    def test_output_file_leaves_the_input_alone(self, cwd, config_toml):
        before = (cwd / config_toml).read_bytes()
        result = runner.invoke(app, ["format", str(config_toml), "-o", "tidy.toml"])
        assert result.exit_code == 0
        assert (cwd / config_toml).read_bytes() == before
        assert (cwd / "tidy.toml").read_bytes() == before

    def test_is_a_pure_reformat(self, cwd, config_toml, namelists):
        """The namelists written before and after a reformat must agree."""
        runner.invoke(app, ["convert", "toml2nml", str(config_toml), "-o", "before"])
        runner.invoke(app, ["format", str(config_toml), "-i", "-q"])
        runner.invoke(app, ["convert", "toml2nml", str(config_toml), "-o", "after"])
        for path in sorted((cwd / "before").glob("*.nml")):
            assert path.read_text() == (cwd / "after" / path.name).read_text()

    def test_a_flat_config_is_canonicalised_to_the_grouped_form(self, cwd, namelists):
        runner.invoke(
            app, ["convert", "nml2toml", str(namelists), "-o", "flat.toml", "--flat"]
        )
        result = runner.invoke(app, ["format", "flat.toml", "-i", "-q"])
        assert result.exit_code == 0
        assert "[[pft]]" in (cwd / "flat.toml").read_text()

    def test_enums_are_written_as_names(self, cwd, config_toml):
        assert b'soilhc_method = "' in self.formatted(cwd, str(config_toml), "-i", "-q")

    def test_refuses_to_write_an_invalid_config_and_leaves_it_alone(self, cwd):
        broken = cwd / "config.toml"
        broken.write_text('[jules_soil.jules_soil]\nsm_levels = "not a number"\n')
        before = broken.read_bytes()
        result = runner.invoke(app, ["format", "config.toml", "--in-place"])
        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert broken.read_bytes() == before

    def test_malformed_toml_is_left_alone(self, cwd):
        broken = cwd / "config.toml"
        broken.write_text("this is not = = toml\n")
        result = runner.invoke(app, ["format", "config.toml", "-i"])
        assert result.exit_code == 1
        assert broken.read_text() == "this is not = = toml\n"

    def test_no_destination_is_a_usage_error(self, cwd, config_toml):
        result = runner.invoke(app, ["format", str(config_toml)])
        assert result.exit_code == 2
        assert "--in-place" in result.output

    def test_both_destinations_is_a_usage_error(self, cwd, config_toml):
        result = runner.invoke(
            app, ["format", str(config_toml), "-o", "out.toml", "--in-place"]
        )
        assert result.exit_code == 2
        assert not (cwd / "out.toml").exists()

    def test_refuses_to_overwrite_the_output_without_the_flag(self, cwd, config_toml):
        args = ["format", str(config_toml), "-o", "tidy.toml"]
        assert runner.invoke(app, args).exit_code == 0
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert "--overwrite" in result.output
        assert runner.invoke(app, [*args, "--overwrite"]).exit_code == 0

    def test_a_directory_argument_is_a_usage_error(self, cwd, namelists):
        result = runner.invoke(app, ["format", str(namelists), "-i"])
        assert result.exit_code == 2

    def test_strict_exits_one(self, cwd, config_toml):
        path = cwd / config_toml
        text = path.read_text().replace(
            "[jules_soil.jules_soil]", "[jules_soil.jules_soil]\nnonsense = 1"
        )
        assert "nonsense" in text
        path.write_text(text)
        result = runner.invoke(app, ["format", str(config_toml), "-i", "--strict"])
        assert result.exit_code == 1
        assert path.read_text() == text
        # Without --strict the unknown member is dropped, which is data loss the
        # report has to name: a reformat is otherwise meant to change nothing.
        result = runner.invoke(app, ["format", str(config_toml), "-i"])
        assert result.exit_code == 0
        assert "UnknownNamelistKeyWarning" in result.output
        assert "nonsense" not in path.read_text()

    def test_leaves_no_temporary_file_behind(self, cwd, config_toml):
        runner.invoke(app, ["format", str(config_toml), "-i", "-q"])
        assert sorted(p.name for p in cwd.glob(".*")) == []


class TestRose2Nml:
    def test_happy_path(self, cwd):
        result = runner.invoke(
            app, ["convert", "rose2nml", str(DATA / f"{CORPUS}.conf"), "-o", "nml"]
        )
        assert result.exit_code == 0
        assert len(list((cwd / "nml").glob("*.nml"))) == 35
        assert runner.invoke(app, ["validate", "nml", "-q"]).exit_code == 0

    def test_unresolved_environment_variables_are_named(self, cwd):
        result = runner.invoke(
            app, ["convert", "rose2nml", str(DATA / f"{CORPUS}.conf"), "-o", "nml"]
        )
        assert "Unresolved environment variables" in result.output
        assert "$DUMP_FILE" in result.output
        assert "$LOOBOS_INSTALL_DIR" in result.output
        assert "will fail validation as a bad path" in result.output

    def test_no_report_when_every_variable_is_bound(self, cwd, monkeypatch):
        for name in ("DUMP_FILE", "LOOBOS_INSTALL_DIR", "ROSE_TASK_NAME"):
            monkeypatch.setenv(name, "bound")
        result = runner.invoke(
            app, ["convert", "rose2nml", str(DATA / f"{CORPUS}.conf"), "-o", "nml"]
        )
        assert result.exit_code == 0
        assert "Unresolved environment variables" not in result.output

    def test_on_unbound_empty_leaves_no_references_behind(self, cwd):
        runner.invoke(
            app,
            [
                "convert",
                "rose2nml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "nml",
                "--on-unbound",
                "empty",
            ],
        )
        text = (cwd / "nml" / "drive.nml").read_text()
        assert "$" not in text

    def test_on_unbound_error_exits_one(self, cwd):
        result = runner.invoke(
            app,
            [
                "convert",
                "rose2nml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "nml",
                "--on-unbound",
                "error",
            ],
        )
        assert result.exit_code == 1
        assert "UnboundVariableError" in result.output

    def test_refuses_to_overwrite_without_the_flag(self, cwd):
        args = ["convert", "rose2nml", str(DATA / f"{CORPUS}.conf"), "-o", "nml"]
        assert runner.invoke(app, args).exit_code == 0
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert "--overwrite" in result.output
        assert runner.invoke(app, [*args, "--overwrite"]).exit_code == 0

    def test_missing_conf_is_a_usage_error(self, cwd):
        result = runner.invoke(
            app, ["convert", "rose2nml", "nowhere.conf", "-o", "nml"]
        )
        assert result.exit_code == 2

    def test_missing_output_option_is_a_usage_error(self, cwd):
        result = runner.invoke(
            app, ["convert", "rose2nml", str(DATA / f"{CORPUS}.conf")]
        )
        assert result.exit_code == 2


class TestRose2Toml:
    def test_happy_path(self, cwd):
        result = runner.invoke(
            app,
            [
                "convert",
                "rose2toml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "config.toml",
            ],
        )
        assert result.exit_code == 0
        assert "pft" in (cwd / "config.toml").read_text()
        assert runner.invoke(app, ["validate", "config.toml", "-q"]).exit_code == 0

    def test_flat_form(self, cwd):
        result = runner.invoke(
            app,
            [
                "convert",
                "rose2toml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "flat.toml",
                "--flat",
            ],
        )
        assert result.exit_code == 0
        assert "[[pft]]" not in (cwd / "flat.toml").read_text()
        assert runner.invoke(app, ["validate", "flat.toml", "-q"]).exit_code == 0

    def test_reports_unresolved_variables(self, cwd):
        result = runner.invoke(
            app,
            [
                "convert",
                "rose2toml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "config.toml",
            ],
        )
        assert "$ROSE_TASK_NAME" in result.output

    def test_refuses_to_overwrite_without_the_flag(self, cwd):
        args = [
            "convert",
            "rose2toml",
            str(DATA / f"{CORPUS}.conf"),
            "-o",
            "config.toml",
        ]
        assert runner.invoke(app, args).exit_code == 0
        assert runner.invoke(app, args).exit_code == 1
        assert runner.invoke(app, [*args, "--overwrite"]).exit_code == 0

    def test_strict_exits_one(self, cwd):
        result = runner.invoke(
            app,
            [
                "convert",
                "rose2toml",
                str(DATA / f"{CORPUS}.conf"),
                "-o",
                "config.toml",
                "--strict",
            ],
        )
        assert result.exit_code == 1


class TestToml2Nml:
    def test_happy_path(self, cwd, config_toml):
        result = runner.invoke(
            app, ["convert", "toml2nml", str(config_toml), "-o", "out"]
        )
        assert result.exit_code == 0
        assert len(list((cwd / "out").glob("*.nml"))) == 29
        assert runner.invoke(app, ["validate", "out", "-q"]).exit_code == 0

    def test_refuses_to_overwrite_without_the_flag(self, cwd, config_toml):
        args = ["convert", "toml2nml", str(config_toml), "-o", "out"]
        assert runner.invoke(app, args).exit_code == 0
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert runner.invoke(app, [*args, "--overwrite"]).exit_code == 0

    def test_a_directory_argument_is_a_usage_error(self, cwd, namelists):
        result = runner.invoke(
            app, ["convert", "toml2nml", str(namelists), "-o", "out"]
        )
        assert result.exit_code == 2


class TestNml2Toml:
    def test_happy_path(self, cwd, namelists):
        result = runner.invoke(
            app, ["convert", "nml2toml", str(namelists), "-o", "c.toml"]
        )
        assert result.exit_code == 0
        assert "[[pft]]" in (cwd / "c.toml").read_text()
        assert runner.invoke(app, ["validate", "c.toml", "-q"]).exit_code == 0

    def test_flat_form_round_trips(self, cwd, namelists):
        result = runner.invoke(
            app,
            ["convert", "nml2toml", str(namelists), "-o", "flat.toml", "--flat"],
        )
        assert result.exit_code == 0
        assert "[[pft]]" not in (cwd / "flat.toml").read_text()
        assert runner.invoke(app, ["validate", "flat.toml", "-q"]).exit_code == 0

    def test_refuses_to_overwrite_without_the_flag(self, cwd, namelists):
        args = ["convert", "nml2toml", str(namelists), "-o", "c.toml"]
        assert runner.invoke(app, args).exit_code == 0
        assert runner.invoke(app, args).exit_code == 1

    def test_a_file_argument_is_a_usage_error(self, cwd, config_toml):
        result = runner.invoke(
            app, ["convert", "nml2toml", str(config_toml), "-o", "c.toml"]
        )
        assert result.exit_code == 2

    def test_invalid_namelists_exit_one(self, cwd, namelists):
        break_namelist(cwd / namelists)
        result = runner.invoke(
            app, ["convert", "nml2toml", str(namelists), "-o", "c.toml"]
        )
        assert result.exit_code == 1
        assert not (cwd / "c.toml").exists()
