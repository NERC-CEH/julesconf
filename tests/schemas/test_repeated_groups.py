"""Tests for namelist groups JULES repeats: output profiles and friends.

Fortran lets one group appear several times in a file, and JULES relies on it:
`jules_output_profile` occurs `nprofiles` times, `jules_prescribed_dataset`
`n_datasets` times, `jules_deposition_species` `ndry_dep_species` times.
julesconf models each as a list of blocks, normalised at the
`NamelistFileHandler` boundary so that the one-vs-many ambiguity in `f90nml`'s
representation never reaches the schemas.

The corpus (`tests/rose/test_convert.py`) covers repeated output profiles and
prescribed datasets against real configurations. **`jules_deposition_species`
repeats nowhere in the corpus** -- the one deposition app has its species
sections `!!`-ignored -- so its cover, and that of its `rsurf_std_io`
`ListLen("ntype")` annotation, is synthetic and lives here.
"""

import warnings

import pytest
from conftest import minimal_valid
from pydantic import ValidationError

from julesconf.config import NamelistConfig, NamelistFileHandler
from julesconf.schemas import (
    REPEATABLE_GROUPS,
    InactiveNamelistKeyWarning,
    JulesNamelists,
)
from julesconf.schemas.jules_deposition import JulesDepositionSpeciesSpecific


def with_profiles(*profiles: dict) -> dict:
    """A minimal config whose `output.nml` holds the given profiles."""
    data = minimal_valid()
    data["output"] = {
        "jules_output": {"nprofiles": len(profiles)},
        "jules_output_profile": list(profiles),
    }
    return data


def with_species(
    *species: dict, count: int | None = None, flexible: bool = False
) -> dict:
    """A minimal config whose `jules_deposition.nml` holds the given species.

    Args:
        species: One dict per `jules_deposition_species` group.
        count: `ndry_dep_species`, defaulting to the number of groups.
        flexible: Select `flexible_ukca`, the scheme that reads the
            per-species arrays. Set it whenever a group carries
            `rsurf_std_io`, or the member is inactive and warns.
    """
    data = minimal_valid()
    deposition = {
        "l_deposition": True,
        "ndry_dep_species": len(species) if count is None else count,
    }
    if flexible:
        deposition["dry_dep_model"] = "flexible_ukca"
    data["jules_deposition"] = {
        "jules_deposition": deposition,
        "jules_deposition_species": list(species),
    }
    return data


# ---------------------------------------------------------------------------
# Which groups repeat
# ---------------------------------------------------------------------------


def test_the_three_groups_jules_repeats_are_the_repeatable_ones():
    assert {
        "jules_output_profile",
        "jules_prescribed_dataset",
        "jules_deposition_species",
    } == REPEATABLE_GROUPS


def test_species_specific_is_not_a_repeated_group():
    """`JULES_DEPOSITION_SPECIES_SPECIFIC` is read once, unlike its sibling.

    The rose file definition is `namelist:jules_deposition
    (namelist:jules_deposition_species(:))
    (namelist:jules_deposition_species_specific)` -- the repeat marker is on
    the species group only.
    """
    assert "jules_deposition_species_specific" not in REPEATABLE_GROUPS
    config = JulesNamelists.model_validate(minimal_valid())
    assert isinstance(
        config.jules_deposition.jules_deposition_species_specific,
        JulesDepositionSpeciesSpecific,
    )


def test_species_specific_members_are_read_by_the_flexible_scheme_only():
    data = with_species({"dep_species_name_io": "O3"})
    data["jules_deposition"]["jules_deposition_species_specific"] = {
        "cuticle_o3_io": 5000.0
    }

    with pytest.warns(InactiveNamelistKeyWarning, match="dry_dep_model"):
        JulesNamelists.model_validate(data)

    data["jules_deposition"]["jules_deposition"]["dry_dep_model"] = "flexible_ukca"
    with warnings.catch_warnings():
        warnings.simplefilter("error", InactiveNamelistKeyWarning)
        config = JulesNamelists.model_validate(data)
    specific = config.jules_deposition.jules_deposition_species_specific
    assert specific.cuticle_o3_io == 5000.0


def test_species_specific_ntype_arrays_are_length_checked():
    """`ch4_up_flux_io` carries `ListLen("ntype")`, so a short array fails."""
    data = with_species({"dep_species_name_io": "CH4"})
    data["jules_deposition"]["jules_deposition"]["dry_dep_model"] = "flexible_ukca"
    data["jules_deposition"]["jules_deposition_species_specific"] = {
        "ch4_up_flux_io": [0.0, 1.0]
    }

    with pytest.raises(ValidationError, match="ch4_up_flux_io"):
        JulesNamelists.model_validate(data)


# ---------------------------------------------------------------------------
# The handler boundary
# ---------------------------------------------------------------------------


class TestHandler:
    def test_a_single_occurrence_reads_as_a_one_element_list(self, tmp_path):
        path = tmp_path / "output.nml"
        path.write_text(
            "&jules_output\nnprofiles=1,\n/\n&jules_output_profile\nnvars=0,\n/\n"
        )

        data = NamelistFileHandler().read(path)
        assert data["jules_output_profile"] == [{"nvars": 0}]

    def test_several_occurrences_read_in_file_order(self, tmp_path):
        path = tmp_path / "output.nml"
        path.write_text(
            "&jules_output_profile\nprofile_name='a',\n/\n"
            "&jules_output_profile\nprofile_name='b',\n/\n"
            "&jules_output_profile\nprofile_name='c',\n/\n"
        )

        data = NamelistFileHandler().read(path)
        assert [block["profile_name"] for block in data["jules_output_profile"]] == [
            "a",
            "b",
            "c",
        ]

    def test_no_occurrence_at_all_is_simply_absent(self, tmp_path):
        path = tmp_path / "output.nml"
        path.write_text("&jules_output\nnprofiles=0,\n/\n")

        assert "jules_output_profile" not in NamelistFileHandler().read(path)

    def test_a_list_is_written_as_that_many_groups(self, tmp_path):
        path = tmp_path / "output.nml"
        NamelistFileHandler().write(
            path,
            {
                "jules_output": {"nprofiles": 2},
                "jules_output_profile": [{"profile_name": "a"}, {"profile_name": "b"}],
            },
        )

        assert path.read_text().count("&jules_output_profile") == 2
        assert "_grp_" not in path.read_text()

    def test_an_empty_list_writes_no_group(self, tmp_path):
        path = tmp_path / "output.nml"
        NamelistFileHandler().write(
            path, {"jules_output": {"nprofiles": 0}, "jules_output_profile": []}
        )

        assert "&jules_output_profile" not in path.read_text()

    def test_write_then_read_is_a_round_trip(self, tmp_path):
        """Multi-element lists only: a one-element array is indistinguishable
        from a scalar in Fortran, and un-doing that is the schemas' job."""
        path = tmp_path / "output.nml"
        data = {
            "jules_output": {"nprofiles": 3},
            "jules_output_profile": [
                {"profile_name": "a", "nvars": 2, "var": ["gpp", "smcl"]},
                {"profile_name": "b", "nvars": 0},
                {"profile_name": "c", "nvars": 2, "var": ["smcl", "t_soil"]},
            ],
        }
        NamelistFileHandler().write(path, data)

        assert NamelistFileHandler().read(path) == data

    def test_a_group_julesconf_holds_one_of_keeps_the_grp_mangling(self, tmp_path):
        """The handler must not silently choose one; the schemas warn instead."""
        path = tmp_path / "output.nml"
        path.write_text(
            "&jules_output\nrun_id='a',\n/\n&jules_output\nrun_id='b',\n/\n"
        )

        data = NamelistFileHandler().read(path)
        assert set(data) == {"_grp_jules_output_0", "_grp_jules_output_1"}


# ---------------------------------------------------------------------------
# The counting members
# ---------------------------------------------------------------------------


class TestCounts:
    def test_matching_counts_validate(self):
        config = JulesNamelists.model_validate(with_profiles({}, {}, {}))
        assert len(config.output.jules_output_profile) == 3

    def test_too_few_groups_is_an_error_naming_both_numbers(self):
        data = with_profiles({}, {})
        data["output"]["jules_output"]["nprofiles"] = 3
        with pytest.raises(
            ValidationError, match=r"occurs 2 time\(s\).*nprofiles is 3"
        ):
            JulesNamelists.model_validate(data)

    def test_surplus_groups_are_kept_and_reported(self):
        """`nprofiles = 1` with three profiles is legal; JULES reads the first."""
        data = with_profiles({}, {"profile_name": "spare"}, {"profile_name": "spare2"})
        data["output"]["jules_output"]["nprofiles"] = 1

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            config = JulesNamelists.model_validate(data)

        assert len(config.output.jules_output_profile) == 3
        inactive = [
            entry
            for entry in caught
            if issubclass(entry.category, InactiveNamelistKeyWarning)
            and "jules_output_profile" in str(entry.message)
        ]
        assert len(inactive) == 1
        assert "ignore the remaining 2" in str(inactive[0].message)

    def test_an_empty_surplus_group_is_silent(self):
        """The empty `&jules_prescribed_dataset /` placeholder is not a smell."""
        data = minimal_valid()
        data["prescribed_data"] = {
            "jules_prescribed": {"n_datasets": 0},
            "jules_prescribed_dataset": [{}],
        }
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            JulesNamelists.model_validate(data)

        assert not [
            entry
            for entry in caught
            if issubclass(entry.category, InactiveNamelistKeyWarning)
        ]

    def test_datasets_are_counted_by_n_datasets(self):
        data = minimal_valid()
        data["prescribed_data"] = {
            "jules_prescribed": {"n_datasets": 2},
            "jules_prescribed_dataset": [{"nvars": 0}],
        }
        with pytest.raises(ValidationError, match="n_datasets is 2"):
            JulesNamelists.model_validate(data)

    def test_species_are_counted_by_ndry_dep_species(self):
        with pytest.raises(ValidationError, match="ndry_dep_species is 2"):
            JulesNamelists.model_validate(with_species({}, count=2))

    def test_an_unset_species_count_is_taken_as_zero(self):
        data = with_species({"dep_species_name_io": "O3"})
        del data["jules_deposition"]["jules_deposition"]["ndry_dep_species"]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            JulesNamelists.model_validate(data)

        assert any("unset, so taken as 0" in str(entry.message) for entry in caught)


# ---------------------------------------------------------------------------
# Per-element sibling dimensions
# ---------------------------------------------------------------------------


class TestPerElementDims:
    def test_each_profile_is_checked_against_its_own_nvars(self):
        """Two profiles, two different `nvars`, both correct."""
        JulesNamelists.model_validate(
            with_profiles(
                {"nvars": 1, "var": ["gpp"]},
                {"nvars": 3, "var": ["smcl", "t_soil", "gpp"]},
            )
        )

    def test_the_second_profile_is_checked_too(self):
        """The bug this closes: only the first profile used to be validated."""
        with pytest.raises(
            ValidationError,
            match=r"output\.jules_output_profile\(2\)\.var has 2 element\(s\),"
            r" expected nvars=3",
        ):
            JulesNamelists.model_validate(
                with_profiles(
                    {"nvars": 1, "var": ["gpp"]},
                    {"nvars": 3, "var": ["smcl", "t_soil"]},
                )
            )

    def test_a_profiles_nvars_does_not_leak_into_its_neighbour(self):
        """Profile 1 satisfying `nvars` must not excuse profile 2 breaking it."""
        with pytest.raises(ValidationError, match=r"jules_output_profile\(2\)"):
            JulesNamelists.model_validate(
                with_profiles(
                    {"nvars": 2, "var": ["gpp", "smcl"]},
                    {"nvars": 2, "var": ["gpp"]},
                )
            )

    def test_per_element_defaults_expand_per_profile(self):
        """`output_type` fills to each profile's own `nvars`, not the first's."""
        config = JulesNamelists.model_validate(
            with_profiles(
                {"nvars": 1, "var": ["gpp"]},
                {"nvars": 3, "var": ["smcl", "t_soil", "gpp"]},
            )
        )
        written = config.to_namelist_dict()["output"]["jules_output_profile"]

        assert written[0]["output_type"] == ["S"]
        assert written[1]["output_type"] == ["S", "S", "S"]

    def test_species_rsurf_std_is_checked_per_species(self):
        """`ListLen("ntype")` inside a repeated group: one array per species."""
        JulesNamelists.model_validate(
            with_species(
                {"dep_species_name_io": "O3", "rsurf_std_io": [1.0] * 9},
                {"dep_species_name_io": "NO2", "rsurf_std_io": [2.0] * 9},
                flexible=True,
            )
        )

        with pytest.raises(
            ValidationError,
            match=r"jules_deposition_species\(2\)\.rsurf_std_io has 8",
        ):
            JulesNamelists.model_validate(
                with_species(
                    {"rsurf_std_io": [1.0] * 9},
                    {"rsurf_std_io": [2.0] * 8},
                    flexible=True,
                )
            )


# ---------------------------------------------------------------------------
# Round-trips
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def make(self) -> JulesNamelists:
        """A config with three distinguishable profiles and two species."""
        config = with_profiles(
            {"profile_name": "a", "nvars": 1, "var": ["gpp"], "output_period": 1800},
            {"profile_name": "b", "nvars": 2, "var": ["smcl", "t_soil"]},
            {"profile_name": "c", "nvars": 0, "file_period": -1},
        )
        config["jules_deposition"] = with_species(
            {"dep_species_name_io": "O3", "rsurf_std_io": [1.0] * 9},
            {"dep_species_name_io": "NO2", "rsurf_std_io": [2.0] * 9},
            flexible=True,
        )["jules_deposition"]
        return JulesNamelists.model_validate(config)

    def test_namelists_round_trip_preserves_every_group(self, tmp_path):
        original = self.make()
        original.to_namelists(tmp_path, overwrite_ok=True)
        back = JulesNamelists.from_namelists(tmp_path)

        # Writing adds every default julesconf holds, so the blocks are a
        # superset rather than equal; what must survive is each profile's own
        # content, in order.
        assert [p.profile_name for p in back.output.jules_output_profile] == [
            "a",
            "b",
            "c",
        ]
        for written, source in zip(
            back.output.jules_output_profile,
            original.output.jules_output_profile,
            strict=True,
        ):
            assert written.nvars == source.nvars
            assert written.var == source.var
            assert written.file_period == source.file_period
        assert [
            s.dep_species_name_io
            for s in back.jules_deposition.jules_deposition_species
        ] == ["O3", "NO2"]
        assert [
            s.rsurf_std_io for s in back.jules_deposition.jules_deposition_species
        ] == [[1.0] * 9, [2.0] * 9]

    def test_the_written_namelists_have_one_group_per_entry(self, tmp_path):
        self.make().to_namelists(tmp_path, overwrite_ok=True)
        text = (tmp_path / "output.nml").read_text()

        assert text.count("&jules_output_profile") == 3
        assert text.index("'a'") < text.index("'b'") < text.index("'c'")

    def test_namelists_to_toml_to_namelists_is_identical(self, tmp_path):
        original = self.make()
        direct, via_toml = tmp_path / "direct", tmp_path / "via_toml"
        original.to_namelists(direct)

        for grouped in (True, False):
            path = tmp_path / f"config-{grouped}.toml"
            original.to_toml(path, grouped=grouped)
            JulesNamelists.from_toml(path).to_namelists(via_toml, overwrite_ok=True)
            assert NamelistConfig().read(direct) == NamelistConfig().read(via_toml)

    def test_the_toml_form_is_an_array_of_tables(self, tmp_path):
        path = tmp_path / "config.toml"
        self.make().to_toml(path)

        assert path.read_text().count("[[output.jules_output_profile]]") == 3

    def test_a_single_profile_is_still_an_array_of_tables(self, tmp_path):
        """No scalar-or-list coercion: one profile is a one-element array."""
        path = tmp_path / "config.toml"
        JulesNamelists.model_validate(with_profiles({"nvars": 0})).to_toml(path)

        assert "[[output.jules_output_profile]]" in path.read_text()

    def test_a_bare_table_is_rejected(self):
        """A config must say `[[...]]`, even for one profile."""
        data = with_profiles({})
        data["output"]["jules_output_profile"] = {"profile_name": "a"}
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            JulesNamelists.model_validate(data)
