"""Tests for scripts/rose_meta_extract.py.

Hermetic: nothing here needs the (gitignored) `reference/jules` checkout or the
network. The merge and rule-splitting logic is exercised against tiny
hand-written metadata trees, and everything else against the committed extract.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
EXTRACT_PATH = REPO_ROOT / "tests" / "data" / "rose_meta" / "vn7.9.json"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import rose_meta_extract as rme  # noqa: E402


@pytest.fixture(scope="module")
def extract() -> dict:
    """The committed vn7.9 extract."""
    return json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))


def write_package(root: Path, name: str, text: str) -> None:
    """Write a `rose-meta.conf` for a package under a metadata root."""
    path = root / name / "rose-meta.conf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- rule splitter


def test_split_rules_separates_on_semicolons():
    value = (
        "this == 1 and namelist:jules_vegetation=l_triffid == '.true.';\n"
        "this == 2 and namelist:jules_vegetation=l_triffid != '.true.';"
    )
    rules = rme.split_rules("namelist:a=b", "fail-if", value)
    assert [rule["expression"] for rule in rules] == [
        "this == 1 and namelist:jules_vegetation=l_triffid == '.true.'",
        "this == 2 and namelist:jules_vegetation=l_triffid != '.true.'",
    ]
    assert [rule["id"] for rule in rules] == [
        "namelist:a=b#fail-if#1",
        "namelist:a=b#fail-if#2",
    ]


def test_split_rules_extracts_the_comment_after_the_separator_as_a_reason():
    # The reason is written after the `;`, so it belongs to the rule before it.
    value = "this == 1;  # Can't use 1-pool with TRIFFID\nthis == 2;  # Nor 4-pool"
    first, second = rme.split_rules("namelist:a=b", "fail-if", value)
    assert first["expression"] == "this == 1"
    assert first["reason"] == "Can't use 1-pool with TRIFFID"
    assert second["expression"] == "this == 2"
    assert second["reason"] == "Nor 4-pool"


def test_split_rules_extracts_an_inline_comment_as_a_reason():
    # An unterminated final rule carries its comment on its own line instead.
    (rule,) = rme.split_rules("namelist:a=b", "warn-if", "this == 3 # deprecated")
    assert rule["expression"] == "this == 3"
    assert rule["reason"] == "deprecated"


def test_split_rules_collapses_continuation_whitespace():
    value = "len(this) !=\n   namelist:jules_surface_types=npft"
    (rule,) = rme.split_rules("namelist:a=b", "fail-if", value)
    assert rule["expression"] == "len(this) != namelist:jules_surface_types=npft"


def test_split_rules_splits_trigger_target_from_condition():
    value = (
        "namelist:jules_soil_biogeochem=l_q10: 1, 2;\n"
        "namelist:jules_soil_ecosse=dt_soilc: 3;"
    )
    first, second = rme.split_rules("namelist:a=b", "trigger", value)
    assert first["target"] == "namelist:jules_soil_biogeochem=l_q10"
    assert first["condition"] == "1, 2"
    assert second["target"] == "namelist:jules_soil_ecosse=dt_soilc"
    assert second["condition"] == "3"


def test_rule_hash_is_stable_and_ignores_layout():
    assert rme.rule_hash("this == 1") == rme.rule_hash("this  ==\n   1")
    assert len(rme.rule_hash("this == 1")) == 16


def test_rule_hash_ignores_a_reworded_comment():
    original = rme.split_rules("namelist:a=b", "fail-if", "this == 1 # because")
    reworded = rme.split_rules("namelist:a=b", "fail-if", "this == 1 # different why")
    assert original[0]["hash"] == reworded[0]["hash"]
    assert original[0]["reason"] != reworded[0]["reason"]


def test_rule_hash_changes_when_the_expression_changes():
    original = rme.split_rules("namelist:a=b", "fail-if", "this == 1; # why")
    edited = rme.split_rules("namelist:a=b", "fail-if", "this == 2; # why")
    assert original[0]["hash"] != edited[0]["hash"]


# ------------------------------------------------------------ import resolution


def test_load_metadata_merges_imported_packages(tmp_path: Path):
    write_package(
        tmp_path,
        "shared/vn1.0",
        "[namelist:jules_nvegparm=albsnc_nvg_io]\ntype=real\n",
    )
    write_package(
        tmp_path,
        "standalone/vn1.0",
        "import=shared/vn1.0\n\n[namelist:jules_soil=sm_levels]\ntype=integer\n",
    )
    sections, sources = rme.load_metadata(tmp_path, "standalone/vn1.0")

    assert sources == ["shared/vn1.0", "standalone/vn1.0"]
    assert set(sections) == {
        "namelist:jules_nvegparm=albsnc_nvg_io",
        "namelist:jules_soil=sm_levels",
    }


def test_load_metadata_lets_the_importer_win_setting_by_setting(tmp_path: Path):
    write_package(
        tmp_path,
        "shared/vn1.0",
        "[namelist:jules_vegetation=can_rad_mod]\ntype=integer\ndescription=shared\n",
    )
    write_package(
        tmp_path,
        "standalone/vn1.0",
        "import=shared/vn1.0\n\n"
        "[namelist:jules_vegetation=can_rad_mod]\ndescription=standalone\nvalues=1,4\n",
    )
    sections, _ = rme.load_metadata(tmp_path, "standalone/vn1.0")
    section = sections["namelist:jules_vegetation=can_rad_mod"]

    assert section["description"] == "standalone"
    assert section["values"] == "1,4"
    # A setting only the shared package gives survives; the section is not
    # replaced wholesale.
    assert section["type"] == "integer"


def test_load_metadata_applies_imports_in_the_order_listed(tmp_path: Path):
    for name in ("first", "second"):
        write_package(
            tmp_path, f"{name}/vn1.0", f"[namelist:a=b]\ndescription={name}\n"
        )
    write_package(tmp_path, "top/vn1.0", "import=first/vn1.0\n      =second/vn1.0\n")
    sections, sources = rme.load_metadata(tmp_path, "top/vn1.0")

    assert sources == ["first/vn1.0", "second/vn1.0", "top/vn1.0"]
    assert sections["namelist:a=b"]["description"] == "second"


def test_load_metadata_drops_ignored_settings(tmp_path: Path):
    write_package(tmp_path, "p/vn1.0", "[namelist:a=b]\ntype=real\n!kind=default\n")
    sections, _ = rme.load_metadata(tmp_path, "p/vn1.0")
    assert sections["namelist:a=b"] == {"type": "real"}


def test_load_metadata_rejects_a_missing_package(tmp_path: Path):
    write_package(tmp_path, "top/vn1.0", "import=absent/vn1.0\n")
    with pytest.raises(FileNotFoundError, match=r"absent/vn1\.0"):
        rme.load_metadata(tmp_path, "top/vn1.0")


def test_build_extract_classifies_sections(tmp_path: Path):
    write_package(
        tmp_path / rme.META_DIR,
        f"{rme.STANDALONE}/vn1.0",
        "[command=default]\nvalues=jules.exe\n\n"
        "[namelist:jules_soil]\ntitle=Soil\n\n"
        "[namelist:jules_soil=sm_levels]\ntype=integer\nrange=1:\nsort-key=a\n",
    )
    data = rme.build_extract(tmp_path, "vn1.0")

    assert data["blocks"] == {"jules_soil": {"title": "Soil"}}
    assert data["fields"]["jules_soil=sm_levels"] == {
        "block": "jules_soil",
        "member": "sm_levels",
        "type": "integer",
        "range": "1:",
        "range_segments": [{"min": 1.0, "max": None}],
    }
    assert data["counts"]["discarded_sections"] == 1
    assert data["provenance"]["version"] == "vn1.0"


# -------------------------------------------------------------- parsing helpers


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0:", [{"min": 0.0, "max": None}]),
        ("9:11", [{"min": 9.0, "max": 11.0}]),
        (":10", [{"min": None, "max": 10.0}]),
        ("-1,1:", [{"min": -1.0, "max": -1.0}, {"min": 1.0, "max": None}]),
        ("this>0", None),
    ],
)
def test_parse_range(value, expected):
    assert rme.parse_range(value) == expected


def test_len_rule_dims_reads_both_spellings():
    entry = {
        "rules": [
            {
                "kind": "fail-if",
                "expression": "len(this) != namelist:jules_surface_types=npft",
            },
            {
                "kind": "fail-if",
                "expression": "len(this) != (namelist:jules_surface_types=nnvg)",
            },
            {"kind": "fail-if", "expression": "len(this) != (npft)+(nnvg)"},
            {"kind": "trigger", "expression": "namelist:a=b: 1"},
        ]
    }
    assert rme.len_rule_dims(entry) == [
        ("jules_surface_types", "npft"),
        ("jules_surface_types", "nnvg"),
    ]


# ------------------------------------------------------------ committed extract


def test_extract_has_a_provenance_header(extract):
    provenance = extract["provenance"]
    assert provenance["upstream_repo"] == rme.UPSTREAM_REPO
    assert provenance["version"] == rme.DEFAULT_VERSION
    assert provenance["upstream_licence"] == "BSD-3-Clause"
    assert len(provenance["commit"]) == 40
    assert len(provenance["sources"]) == 11
    assert provenance["sources"][-1].endswith(
        f"{rme.STANDALONE}/{rme.DEFAULT_VERSION}/rose-meta.conf"
    )


def test_extract_has_the_expected_section_counts(extract):
    counts = extract["counts"]
    assert counts["sections"] == 1038
    assert counts["fields"] == 963
    assert counts["blocks"] == 62
    assert (
        counts["sections"]
        == counts["fields"] + counts["blocks"] + (counts["discarded_sections"])
    )
    assert len(extract["fields"]) == counts["fields"]
    assert len(extract["blocks"]) == counts["blocks"]


def test_extract_includes_blocks_that_only_the_shared_packages_define(extract):
    # jules_nvegparm exists only in jules-shared/jules-nvegparm, so reading the
    # standalone file alone would silently drop the whole namelist.
    assert "jules_nvegparm" in extract["blocks"]
    assert "jules_nvegparm=albsnc_nvg_io" in extract["fields"]


def test_extract_field_entry_is_normalised(extract):
    entry = extract["fields"]["jules_soil_biogeochem=soil_bgc_model"]
    assert entry["block"] == "jules_soil_biogeochem"
    assert entry["member"] == "soil_bgc_model"
    assert entry["compulsory"] is True
    fail_ifs = [rule for rule in entry["rules"] if rule["kind"] == "fail-if"]
    assert len(fail_ifs) == 3
    assert fail_ifs[0]["reason"] == "Can't use 1-pool with TRIFFID"
    assert all(len(rule["hash"]) == 16 for rule in entry["rules"])
    assert any(rule["kind"] == "trigger" for rule in entry["rules"])


def test_extract_discards_gui_only_settings(extract):
    for entry in extract["fields"].values():
        assert not set(entry) & {"sort-key", "ns", "widget[rose-config-edit]"}


def test_extract_rule_ids_are_unique(extract):
    ids = [
        rule["id"]
        for entry in extract["fields"].values()
        for rule in entry.get("rules", ())
    ]
    assert len(ids) == extract["counts"]["rules"]
    assert len(ids) == len(set(ids))


def test_extract_is_written_sorted_for_stable_diffs():
    text = EXTRACT_PATH.read_text(encoding="utf-8")
    assert text == json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n"


# ------------------------------------------------------------------- the audit


@pytest.fixture(scope="module")
def audit(extract) -> rme.Audit:
    """The audit of the committed extract against the current schemas."""
    return rme.run_audit(extract)


def test_audit_counts_blocks_and_members(audit):
    counts = audit.counts
    assert counts["blocks_shared"] == 54
    assert counts["blocks_in_schemas"] == counts["blocks_shared"] + len(
        audit.schema_only_blocks
    )
    assert counts["blocks_in_metadata"] == counts["blocks_shared"] + len(
        audit.metadata_only_blocks
    )
    assert counts["members_missing"] > 0
    assert counts["members_in_metadata"] > counts["members_in_schemas"]


def test_audit_excludes_postponed_namelists(audit):
    reported = set(audit.metadata_only_blocks) | set(audit.schema_only_blocks)
    assert not any(name.startswith("cable_") for name in reported)
    assert "oasis_rivers" not in reported
    assert "jules_red" not in reported


def test_audit_reports_no_list_length_disagreements(audit):
    # The only one was `jules_cropparm=cfrac_s_io`, where the metadata says
    # ncpft and the user guide says npft. The schemas still follow the user
    # guide for the canonical length but tolerate ncpft on input, which is what
    # every real configuration supplies, so the audit no longer flags it. The
    # upstream contradiction itself is pinned in
    # `tests/schemas/test_cross_namelist.py`.
    assert audit.list_len_mismatches == []


def test_audit_reports_bounds_we_impose_without_metadata_support(audit):
    # The metadata declares the whole of JULES_CROPPARM `type=real` with no
    # `range=`, so every bound we place there is our own, taken from the user
    # guide. `remob_io` is documented as a fraction, so `[0, 1]` is justified;
    # `delta_io` was not, and the bound was a bug -- it must not come back.
    assert any(
        item.startswith("jules_cropparm=remob_io") for item in audit.bounds_unspecified
    )
    assert not any(
        item.startswith("jules_cropparm=delta_io") for item in audit.bounds_unspecified
    )


def test_audit_tolerated_list_lengths_are_not_flagged(audit):
    # The TRIFFID parameters are declared real(npft) but only nnpft values are
    # read, which ListLen models as tolerates=("npft",).
    assert not any(
        item.startswith("jules_triffid=") for item in audit.list_len_mismatches
    )


def test_audit_renders_a_report(audit):
    report = audit.render()
    assert report.endswith("\n")
    assert "julesconf schema audit" in report
    for heading in (
        "Blocks in metadata but not in schemas",
        "Members missing from schemas",
        "Enumerations that disagree",
        "List lengths that disagree",
    ):
        assert heading in report


def test_audit_cli_writes_the_report(tmp_path: Path, capsys):
    destination = tmp_path / "report.txt"
    assert (
        rme.main(["audit", "--extract", str(EXTRACT_PATH), "-o", str(destination)]) == 0
    )
    assert "julesconf schema audit" in destination.read_text(encoding="utf-8")

    assert rme.main(["audit", "--extract", str(EXTRACT_PATH)]) == 0
    assert "julesconf schema audit" in capsys.readouterr().out


# --------------------------------------------------------------------------
# The disposition lockfile
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("len(this) != namelist:jules_surface_types=npft", "npft"),
        ("len(this) != (namelist:jules_soil_props=nvars)", "nvars"),
        (
            "len(this) != (namelist:jules_surface_types=npft +"
            " namelist:jules_surface_types=nnvg)",
            "ntype",
        ),
        ("this == 1 and namelist:jules_vegetation=l_triffid == '.true.'", None),
    ],
)
def test_len_rule_dim(expression, expected):
    assert rme._len_rule_dim(expression) == expected


def test_build_disposition_auto_classifies_a_new_rule(extract):
    entries, counts = rme.build_disposition(extract, {})
    assert counts["added"] == extract["counts"]["rules"]
    assert counts["removed"] == 0

    cable = entries["namelist:cable_pftparm=a1gs_io#fail-if#1"]
    assert cable["status"] == "out-of-scope"

    listlen = entries["namelist:jules_pftparm=canht_ft_io#fail-if#1"]
    assert listlen["status"] == "covered-by-listlen"
    assert listlen["where"] == "ListLen('npft')"


def test_build_disposition_preserves_a_curated_entry(extract):
    rule_id = "namelist:jules_soil_biogeochem=soil_bgc_model#fail-if#1"
    curated = {rule_id: {"status": "implemented", "where": "somewhere", "hash": "old"}}
    entries, counts = rme.build_disposition(extract, curated)
    assert entries[rule_id]["status"] == "implemented"
    assert entries[rule_id]["where"] == "somewhere"
    # The hash is always refreshed from the extract.
    assert entries[rule_id]["hash"] != "old"
    assert counts["added"] == extract["counts"]["rules"] - 1


def test_build_disposition_drops_a_rotten_entry(extract):
    _, counts = rme.build_disposition(extract, {"namelist:gone=away#fail-if#1": {}})
    assert counts["removed"] == 1


def test_render_disposition_round_trips(extract):
    import tomllib

    entries, _ = rme.build_disposition(extract, {})
    text = rme.render_disposition(entries)
    assert text.startswith("# Disposition of every conditional rule")
    assert tomllib.loads(text) == entries


def test_disposition_cli_matches_the_committed_lockfile(tmp_path: Path):
    """Regenerating the lockfile must be a no-op, so a stale one is visible."""
    destination = tmp_path / "rules_disposition.toml"
    destination.write_text(rme.DEFAULT_DISPOSITION.read_text(encoding="utf-8"))
    assert (
        rme.main(
            [
                "disposition",
                "--extract",
                str(EXTRACT_PATH),
                "-o",
                str(destination),
            ]
        )
        == 0
    )
    assert destination.read_text(encoding="utf-8") == rme.DEFAULT_DISPOSITION.read_text(
        encoding="utf-8"
    )


# --------------------------------------------------------------------------
# Drift
# --------------------------------------------------------------------------


def _one_rule_extract(rule_id: str, expression: str, reason: str = "") -> dict:
    rule = {
        "id": rule_id,
        "kind": "fail-if",
        "expression": expression,
        "hash": rme.rule_hash(expression),
    }
    if reason:
        rule["reason"] = reason
    return {
        "provenance": {"version": "vn7.9", "commit": "abc123"},
        "fields": {"block=member": {"block": "b", "member": "m", "rules": [rule]}},
    }


def test_render_drift_reports_nothing_when_identical():
    one = _one_rule_extract("a#fail-if#1", "this == 1")
    _, drifted = rme.render_drift(one, one, {})
    assert not drifted


def test_render_drift_lists_added_removed_and_changed():
    before = _one_rule_extract("a#fail-if#1", "this == 1", "old reason")
    after = _one_rule_extract("a#fail-if#1", "this == 2", "new reason")
    after["fields"]["other"] = {
        "block": "b",
        "member": "n",
        "rules": [
            {
                "id": "b#fail-if#1",
                "kind": "fail-if",
                "expression": "this == 3",
                "hash": rme.rule_hash("this == 3"),
                "reason": "brand new",
            }
        ],
    }
    report, drifted = rme.render_drift(
        before, after, {"a#fail-if#1": {"status": "implemented"}}
    )
    assert drifted
    assert "added: 1  removed: 0  changed: 1" in report
    assert "## Added (1)" in report
    assert "brand new" in report
    assert "was: `this == 1`" in report
    assert "_implemented_" in report


def test_drift_cli_reports_no_drift(tmp_path: Path, capsys):
    assert rme.main(["drift", str(EXTRACT_PATH), "--baseline", str(EXTRACT_PATH)]) == 0
    assert "drift=false" in capsys.readouterr().out


def test_drift_cli_writes_a_report(tmp_path: Path, capsys):
    candidate = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    del candidate["fields"]["jules_soil=l_bedrock"]["rules"]
    destination = tmp_path / "drift.md"
    candidate_path = tmp_path / "upstream.json"
    candidate_path.write_text(json.dumps(candidate))

    assert (
        rme.main(
            [
                "drift",
                str(candidate_path),
                "--baseline",
                str(EXTRACT_PATH),
                "-o",
                str(destination),
            ]
        )
        == 0
    )
    assert "drift=true" in capsys.readouterr().out
    assert "## Removed (4)" in destination.read_text(encoding="utf-8")
