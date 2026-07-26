"""Tests for julesconf.rose._app, the JULES view of a rose config.

The fixtures are hand-written miniatures. The real apps are vendored in
`tests/data/rose_apps/` and exercised by `test_convert.py`.
"""

import textwrap

import pytest

from julesconf.rose import (
    MissingNamelistError,
    RoseApp,
    RoseConfig,
    SourceRef,
    State,
    UnsupportedSourceError,
)
from julesconf.rose._app import block_name


def app(text: str) -> RoseApp:
    """Build a RoseApp from a dedented inline fixture."""
    return RoseApp.from_config(RoseConfig.parse(textwrap.dedent(text).lstrip("\n")))


class TestSourceRef:
    def test_plain_token(self):
        assert SourceRef.parse("namelist:jules_soil") == SourceRef("jules_soil")

    def test_optional_token(self):
        assert SourceRef.parse("(namelist:jules_top)") == SourceRef(
            "jules_top", optional=True
        )

    def test_indexed_token(self):
        assert SourceRef.parse("namelist:jules_output_profile(:)") == SourceRef(
            "jules_output_profile", indexed=True
        )

    def test_optional_indexed_token(self):
        assert SourceRef.parse("(namelist:jules_deposition_species(:))") == SourceRef(
            "jules_deposition_species", optional=True, indexed=True
        )

    @pytest.mark.parametrize("token", ["fs:file.nml", "svn://x/y", "git:a", "junk"])
    def test_unknown_scheme_raises(self, token):
        with pytest.raises(UnsupportedSourceError, match="not a 'namelist:' source"):
            SourceRef.parse(token, "drive.nml")

    def test_optional_unknown_scheme_raises(self):
        with pytest.raises(UnsupportedSourceError):
            SourceRef.parse("(fs:file.nml)")


class TestFromConfig:
    def test_meta_and_command(self):
        parsed = app("""
            meta=jules-standalone/vn8.2

            [command]
            default=rose-jules-run

            [namelist:jules_soil]
            dzsoil_io=0.1
        """)
        assert parsed.meta == "jules-standalone/vn8.2"
        assert parsed.command == {"default": "rose-jules-run"}

    def test_no_meta(self):
        assert app("[command]\ndefault=x\n").meta is None

    def test_files_keyed_by_target(self):
        parsed = app("""
            [file:model_grid.nml]
            source=namelist:jules_input_grid (namelist:jules_z_land)
        """)
        assert parsed.files == {
            "model_grid.nml": [
                SourceRef("jules_input_grid"),
                SourceRef("jules_z_land", optional=True),
            ]
        }

    def test_ignored_file_section_dropped(self):
        parsed = app("""
            [!!file:fire.nml]
            source=namelist:fire_switches
        """)
        assert parsed.files == {}

    def test_namelist_keys_strip_prefix_and_keep_index(self):
        parsed = app("""
            [namelist:jules_soil]
            dzsoil_io=0.1

            [namelist:jules_output_profile(2)]
            profile_name='b'
        """)
        assert list(parsed.namelists) == ["jules_soil", "jules_output_profile(2)"]

    def test_ignored_namelist_section_kept(self):
        parsed = app("[!!namelist:cable_pftparm]\na1gs_io=17*9.0\n")
        assert parsed.namelists["cable_pftparm"].state is State.SYST_IGNORED

    def test_file_section_without_source(self):
        assert app("[file:empty.nml]\n").files == {"empty.nml": []}


class TestResolve:
    def test_required_present(self):
        parsed = app("""
            [file:a.nml]
            source=namelist:jules_soil

            [namelist:jules_soil]
            dzsoil_io=0.1
        """)
        assert parsed.sections_for("a.nml") == ["jules_soil"]

    def test_required_missing_raises(self):
        parsed = app("[file:a.nml]\nsource=namelist:jules_soil\n")
        with pytest.raises(MissingNamelistError, match=r"\[namelist:jules_soil\]"):
            parsed.sections_for("a.nml")

    def test_optional_missing_is_skipped(self):
        parsed = app("[file:a.nml]\nsource=(namelist:jules_top)\n")
        assert parsed.sections_for("a.nml") == []

    def test_optional_ignored_is_skipped(self):
        parsed = app("""
            [file:a.nml]
            source=(namelist:jules_top)

            [!!namelist:jules_top]
            zw_max=6.0
        """)
        assert parsed.sections_for("a.nml") == []

    def test_required_ignored_is_skipped(self):
        """An ignored section is omitted entirely, exactly as rose does."""
        parsed = app("""
            [file:a.nml]
            source=namelist:jules_soil namelist:jules_top

            [namelist:jules_soil]
            dzsoil_io=0.1

            [!namelist:jules_top]
            zw_max=6.0
        """)
        assert parsed.sections_for("a.nml") == ["jules_soil"]

    def test_indexed_expansion_is_numerically_ordered(self):
        parsed = app("""
            [file:a.nml]
            source=namelist:p(:)

            [namelist:p(10)]
            n=10

            [namelist:p(2)]
            n=2

            [namelist:p(1)]
            n=1
        """)
        assert parsed.sections_for("a.nml") == ["p(1)", "p(2)", "p(10)"]

    def test_indexed_expansion_skips_ignored(self):
        parsed = app("""
            [file:a.nml]
            source=namelist:p(:)

            [namelist:p(1)]
            n=1

            [!!namelist:p(2)]
            n=2
        """)
        assert parsed.sections_for("a.nml") == ["p(1)"]

    def test_indexed_expansion_ignores_unrelated_prefixes(self):
        parsed = app("""
            [file:a.nml]
            source=namelist:p(:)

            [namelist:p(1)]
            n=1

            [namelist:p_extra(1)]
            n=2
        """)
        assert parsed.sections_for("a.nml") == ["p(1)"]

    def test_indexed_expansion_of_nothing_is_empty(self):
        parsed = app("[file:a.nml]\nsource=namelist:p(:)\n")
        assert parsed.sections_for("a.nml") == []

    def test_source_order_is_preserved(self):
        parsed = app("""
            [file:a.nml]
            source=namelist:zeta namelist:alpha

            [namelist:alpha]
            n=1

            [namelist:zeta]
            n=2
        """)
        assert parsed.sections_for("a.nml") == ["zeta", "alpha"]

    def test_unknown_target_raises_key_error(self):
        with pytest.raises(KeyError):
            app("[command]\ndefault=x\n").sections_for("nope.nml")


class TestBlockName:
    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("jules_soil", "jules_soil"),
            ("jules_output_profile(2)", "jules_output_profile"),
            ("p(10)", "p"),
        ],
    )
    def test_index_is_stripped(self, key, expected):
        assert block_name(key) == expected


class TestParseFile:
    def test_round_trip_through_disk(self, tmp_path):
        path = tmp_path / "rose-app.conf"
        path.write_text("meta=jules-standalone/vn8.2\n\n[namelist:jules_soil]\nn=1\n")
        parsed = RoseApp.parse_file(path)
        assert parsed.meta == "jules-standalone/vn8.2"
        assert parsed.namelists["jules_soil"].settings["n"].value == "1"
