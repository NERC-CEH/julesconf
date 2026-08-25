"""Tests for julesconf.rose._config, the rose config format layer.

The fixtures here are hand-written miniatures of the real `rose-app.conf`
and `rose-meta.conf` files; the real ones are not vendored into the repo.
"""

import string
import textwrap

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from julesconf.rose import RoseConfig, RoseParseError, Section, Setting, State


def conf(text: str) -> str:
    """Dedent a triple-quoted fixture and drop its leading newline."""
    return textwrap.dedent(text).lstrip("\n")


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


class TestSections:
    def test_single_section(self):
        cfg = RoseConfig.parse(
            conf("""
            [namelist:jules_soil]
            dzsoil_io=0.1,0.25,0.65,2.0
        """)
        )
        assert list(cfg.sections) == ["namelist:jules_soil"]
        section = cfg.sections["namelist:jules_soil"]
        assert section.state is State.NORMAL
        assert section.settings["dzsoil_io"].value == "0.1,0.25,0.65,2.0"

    def test_user_ignored_section(self):
        cfg = RoseConfig.parse("[!namelist:jules_irrig]\nirr_crop=1\n")
        assert cfg.sections["namelist:jules_irrig"].state is State.USER_IGNORED

    def test_system_ignored_section(self):
        cfg = RoseConfig.parse("[!!namelist:cable_pftparm]\na1gs_io=17*9.0\n")
        assert cfg.sections["namelist:cable_pftparm"].state is State.SYST_IGNORED

    def test_section_order_preserved(self):
        cfg = RoseConfig.parse("[zeta]\na=1\n\n[alpha]\nb=2\n\n[mu]\nc=3\n")
        assert list(cfg.sections) == ["zeta", "alpha", "mu"]

    def test_empty_section_has_no_settings(self):
        cfg = RoseConfig.parse("[command]\n\n[file:drive.nml]\nsource=x\n")
        assert cfg.sections["command"].settings == {}

    def test_empty_header_returns_to_root(self):
        cfg = RoseConfig.parse("[foo]\na=1\n\n[]\nb=2\n")
        assert cfg.sections["foo"].settings["a"].value == "1"
        assert cfg.root["b"].value == "2"

    def test_section_name_may_contain_equals(self):
        cfg = RoseConfig.parse("[namelist:jules_soil=dzsoil_io]\ntype=real\n")
        assert "namelist:jules_soil=dzsoil_io" in cfg.sections


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


class TestSettings:
    def test_root_settings(self):
        cfg = RoseConfig.parse("meta=jules-standalone/vn7.9\n\n[command]\nd=x\n")
        assert cfg.root["meta"].value == "jules-standalone/vn7.9"
        assert "meta" not in cfg.sections["command"].settings

    def test_user_ignored_key(self):
        cfg = RoseConfig.parse("[s]\n!l_triffid=.false.\n")
        setting = cfg.sections["s"].settings["l_triffid"]
        assert setting.state is State.USER_IGNORED
        assert setting.value == ".false."

    def test_system_ignored_key(self):
        cfg = RoseConfig.parse("[s]\n!!kind=default\n")
        assert cfg.sections["s"].settings["kind"].state is State.SYST_IGNORED

    def test_setting_order_preserved(self):
        cfg = RoseConfig.parse("[s]\nz=1\na=2\nm=3\n")
        assert list(cfg.sections["s"].settings) == ["z", "a", "m"]

    def test_empty_value(self):
        cfg = RoseConfig.parse("[s]\nvar_name=\n")
        assert cfg.sections["s"].settings["var_name"].value == ""

    def test_whitespace_around_assignment_is_stripped(self):
        cfg = RoseConfig.parse("[s]\nkey =  value  \n")
        assert cfg.sections["s"].settings["key"].value == "value"

    def test_value_may_contain_equals(self):
        cfg = RoseConfig.parse("[s]\nfail-if=len(this) != nvars;\n")
        assert cfg.sections["s"].settings["fail-if"].value == "len(this) != nvars;"

    def test_value_may_contain_hash(self):
        # There are no trailing comments: a mid-line '#' is part of the value.
        cfg = RoseConfig.parse("[s]\nurl=http://x/y.html#JULES_SOIL::dzsoil_io\n")
        value = cfg.sections["s"].settings["url"].value
        assert value == "http://x/y.html#JULES_SOIL::dzsoil_io"

    def test_values_are_not_interpreted(self):
        cfg = RoseConfig.parse(
            conf("""
            [s]
            l_triffid=.false.
            output_dir='./output'
            var='S'
            tiles=8*'S'
            rate=5*1.667
            big=0.28e6
        """)
        )
        raw = {k: v.value for k, v in cfg.sections["s"].settings.items()}
        assert raw == {
            "l_triffid": ".false.",
            "output_dir": "'./output'",
            "var": "'S'",
            "tiles": "8*'S'",
            "rate": "5*1.667",
            "big": "0.28e6",
        }
        assert all(isinstance(v, str) for v in raw.values())


# ---------------------------------------------------------------------------
# Continuation lines
# ---------------------------------------------------------------------------


class TestContinuations:
    def test_continuation_with_equals_prefix(self):
        cfg = RoseConfig.parse(
            conf("""
            [s]
            var='b','sathh','satcon',
               ='hcon','albsoil'
        """)
        )
        expected = "'b','sathh','satcon',\n'hcon','albsoil'"
        assert cfg.sections["s"].settings["var"].value == expected

    def test_continuation_without_equals_prefix(self):
        cfg = RoseConfig.parse(
            conf("""
            [s]
            description=This namelist reads the values
                        of parameters for each PFT
        """)
        )
        expected = "This namelist reads the values\nof parameters for each PFT"
        assert cfg.sections["s"].settings["description"].value == expected

    def test_only_one_equals_is_stripped(self):
        cfg = RoseConfig.parse("[s]\nk=a\n  ==b\n")
        assert cfg.sections["s"].settings["k"].value == "a\n=b"

    def test_many_continuation_lines(self):
        cfg = RoseConfig.parse("[s]\nk=1,\n  =2,\n  =3,\n  =4\n")
        assert cfg.sections["s"].settings["k"].value == "1,\n2,\n3,\n4"

    def test_continuation_of_ignored_setting(self):
        cfg = RoseConfig.parse("[s]\n!!clitt_io=20.0,\n          =6.0\n")
        setting = cfg.sections["s"].settings["clitt_io"]
        assert setting.state is State.SYST_IGNORED
        assert setting.value == "20.0,\n6.0"

    def test_continuation_of_root_setting(self):
        cfg = RoseConfig.parse("import=a/vn7.9\n      =b/vn7.9\n")
        assert cfg.root["import"].value == "a/vn7.9\nb/vn7.9"

    def test_indented_line_before_any_setting_is_an_error(self):
        with pytest.raises(RoseParseError):
            RoseConfig.parse("[s]\n   =orphan\n")


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class TestComments:
    def test_comment_attaches_to_following_setting(self):
        cfg = RoseConfig.parse("[s]\n# Entry not in documentation\nurl=x\n")
        assert cfg.sections["s"].settings["url"].comments == [
            " Entry not in documentation"
        ]

    def test_comment_attaches_to_following_section(self):
        cfg = RoseConfig.parse("[a]\nk=1\n\n# moved to jules-shared\n[b]\nk=2\n")
        assert cfg.sections["b"].comments == [" moved to jules-shared"]
        assert cfg.sections["a"].comments == []

    def test_multiple_comments_attach_in_order(self):
        cfg = RoseConfig.parse("[s]\n# one\n# two\nk=1\n")
        assert cfg.sections["s"].settings["k"].comments == [" one", " two"]

    def test_leading_comment_block_attaches_to_file(self):
        cfg = RoseConfig.parse("# Please see the wiki\n\nimport=shared/vn7.9\n")
        assert cfg.comments == [" Please see the wiki"]
        assert cfg.root["import"].comments == []

    def test_blank_line_detaches_comment(self):
        cfg = RoseConfig.parse("[a]\nk=1\n# orphan\n\n[b]\nk=2\n")
        assert cfg.sections["b"].comments == []

    def test_hash_must_be_first_non_space_character(self):
        cfg = RoseConfig.parse("[s]\nk=v # not a comment\n")
        assert cfg.sections["s"].settings["k"].value == "v # not a comment"


# ---------------------------------------------------------------------------
# Duplicate declarations
# ---------------------------------------------------------------------------


class TestDuplicates:
    def test_repeated_section_appends_settings(self):
        cfg = RoseConfig.parse("[s]\na=1\n\n[t]\nb=2\n\n[s]\nc=3\n")
        assert list(cfg.sections) == ["s", "t"]
        assert list(cfg.sections["s"].settings) == ["a", "c"]

    def test_repeated_section_updates_state(self):
        cfg = RoseConfig.parse("[s]\na=1\n\n[!!s]\nc=3\n")
        assert cfg.sections["s"].state is State.SYST_IGNORED

    def test_repeated_key_overrides_value(self):
        cfg = RoseConfig.parse("[s]\na=1\nb=2\na=3\n")
        assert cfg.sections["s"].settings["a"].value == "3"

    def test_repeated_key_keeps_original_position(self):
        cfg = RoseConfig.parse("[s]\na=1\nb=2\na=3\n")
        assert list(cfg.sections["s"].settings) == ["a", "b"]


# ---------------------------------------------------------------------------
# Errors and file loading
# ---------------------------------------------------------------------------


class TestParseErrors:
    def test_line_without_assignment_is_an_error(self):
        with pytest.raises(RoseParseError, match="line 2"):
            RoseConfig.parse("[s]\nnonsense\n")

    def test_error_reports_the_offending_line(self):
        with pytest.raises(RoseParseError) as excinfo:
            RoseConfig.parse("[s]\nk=1\nnonsense\n")
        assert excinfo.value.line_number == 3
        assert excinfo.value.line == "nonsense"


class TestParseFile:
    def test_parse_file(self, tmp_path):
        path = tmp_path / "rose-app.conf"
        path.write_text("meta=jules-standalone/vn7.9\n\n[s]\nk=1\n")
        cfg = RoseConfig.parse_file(path)
        assert cfg.root["meta"].value == "jules-standalone/vn7.9"

    def test_parse_file_matches_parse(self, tmp_path):
        text = "meta=x\n\n[s]\nk=1\n"
        path = tmp_path / "rose-app.conf"
        path.write_text(text)
        assert RoseConfig.parse_file(path) == RoseConfig.parse(text)


# ---------------------------------------------------------------------------
# dump
# ---------------------------------------------------------------------------


class TestDump:
    def test_empty_config_dumps_to_empty_string(self):
        assert RoseConfig().dump() == ""

    def test_blank_line_between_sections(self):
        cfg = RoseConfig.parse("[a]\nk=1\n[b]\nk=2\n")
        assert cfg.dump() == "[a]\nk=1\n\n[b]\nk=2\n"

    def test_continuation_equals_aligns_under_the_original(self):
        cfg = RoseConfig(
            sections={"s": Section(settings={"clitt_io": Setting("20.0,\n6.0")})}
        )
        assert cfg.dump() == "[s]\nclitt_io=20.0,\n        =6.0\n"

    def test_continuation_indent_accounts_for_state_prefix(self):
        setting = Setting("20.0,\n6.0", state=State.SYST_IGNORED)
        cfg = RoseConfig(sections={"s": Section(settings={"clitt_io": setting})})
        assert cfg.dump() == "[s]\n!!clitt_io=20.0,\n          =6.0\n"

    def test_file_comments_are_followed_by_a_blank_line(self):
        cfg = RoseConfig(comments=[" hello"], root={"meta": Setting("x")})
        assert cfg.dump() == "# hello\n\nmeta=x\n"

    def test_root_settings_precede_sections(self):
        cfg = RoseConfig.parse("[s]\nk=1\n\n[]\nmeta=x\n")
        assert cfg.dump() == "meta=x\n\n[s]\nk=1\n"


# ---------------------------------------------------------------------------
# Round trips
# ---------------------------------------------------------------------------

SAMPLE = conf("""
    # Please see the JULES wiki
    #  for how this file is shared

    import=jules-shared/jules-soil/vn7.9
          =jules-shared/jules-snow/vn7.9
    meta=jules-standalone/vn7.9

    [command]
    default=rose-run jules.exe

    # moved to jules-shared
    [!!namelist:cable_pftparm]
    !!clitt_io=20.000000,6.000000,10.000000,
              =2.000000,
              =5*0.000000
    !!kind=default

    [namelist:jules_soil]
    # Entry does not exist in the documentation
    dzsoil_io=0.100000,0.250000,0.650000,2.000000
    l_vg_soil=.false.
    !sm_levels=4
    url=http://x/jules_soil.nml.html#JULES_SOIL::dzsoil_io

    [namelist:jules_output]
    fail-if=len(this) != nvars;
    output_dir='./output'
    var='b','sathh','satcon',
       ='hcon','albsoil'
""")


class TestRoundTrip:
    def test_dump_reproduces_source_byte_for_byte(self):
        assert RoseConfig.parse(SAMPLE).dump() == SAMPLE

    def test_parse_dump_parse_is_idempotent(self):
        once = RoseConfig.parse(SAMPLE)
        twice = RoseConfig.parse(once.dump())
        assert twice == once
        assert twice.dump() == once.dump()


# ---------------------------------------------------------------------------
# Hypothesis property-based round trip
# ---------------------------------------------------------------------------

_KEY_CHARS = string.ascii_lowercase + string.digits + "_-"
_NAME_CHARS = string.ascii_lowercase + string.digits + "_-:()"
_TEXT_CHARS = string.ascii_letters + string.digits + " _-.,*'#=/!()"

states = st.sampled_from(list(State))

# Keys may contain neither whitespace nor '=', and a leading '!' would be read
# back as a state marker.
keys = st.text(alphabet=_KEY_CHARS, min_size=1, max_size=20)

# Section names may contain no brackets, and are stripped of surrounding
# whitespace when read back.
section_names = st.text(alphabet=_NAME_CHARS, min_size=1, max_size=30)

# Values are stripped line by line on the way in, so generated lines carry no
# surrounding whitespace. A continuation line beginning with '=' loses that
# '=' on the way back in -- rose has the same lossiness -- so exclude it.
_value_line = st.text(alphabet=_TEXT_CHARS, max_size=40).map(str.strip)
_continuation_line = _value_line.filter(lambda line: not line.startswith("="))

values = st.builds(
    lambda head, tail: "\n".join([head, *tail]),
    head=_value_line,
    tail=st.lists(_continuation_line, max_size=4),
)

# Comments are stored without their '#' and are stripped of trailing
# whitespace when read back.
comments = st.lists(
    st.text(alphabet=_TEXT_CHARS, max_size=40).map(str.rstrip),
    max_size=3,
)

setting_objects = st.builds(Setting, value=values, state=states, comments=comments)

settings_dicts = st.dictionaries(keys, setting_objects, max_size=5)

section_objects = st.builds(
    Section, state=states, settings=settings_dicts, comments=comments
)

rose_configs = st.builds(
    RoseConfig,
    root=settings_dicts,
    sections=st.dictionaries(section_names, section_objects, max_size=4),
    comments=comments,
)


class TestHypothesisRoundTrip:
    @given(rose_configs)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_of_dump_recovers_the_config(self, cfg):
        assert RoseConfig.parse(cfg.dump()) == cfg

    @given(rose_configs)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_dump_is_stable_under_reparsing(self, cfg):
        text = cfg.dump()
        assert RoseConfig.parse(text).dump() == text
