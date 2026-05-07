# pyright: reportArgumentType=false
"""Tests for julesconf.config module.

Covers NamelistFileHandler, NamelistConfig, AsciiFileHandler,
NetcdfFileHandler, InputFilesConfig, and JulesConfig.
"""

import datetime
import os
import shutil
import string
from contextlib import contextmanager
from pathlib import Path

import f90nml
import numpy
import pytest
import xarray
from dirconf import MISSING
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from julesconf.config import (
    AsciiFileHandler,
    InputFilesConfig,
    JulesConfig,
    NamelistConfig,
    NamelistFileHandler,
    NetcdfFileHandler,
)


@contextmanager
def chdir(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_scalar_values = st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(
        min_value=-1e6,
        max_value=1e6,
        allow_nan=False,
        allow_infinity=False,
        allow_subnormal=False,
    ),
    st.booleans(),
    st.text(
        alphabet=string.ascii_letters + string.digits + " _-",
        min_size=1,
        max_size=30,
    ),
)

_list_values = st.lists(_scalar_values, min_size=1, max_size=10)

_namelist_value = st.one_of(_scalar_values, _list_values)

_namelist_block = st.dictionaries(
    keys=st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=20),
    values=_namelist_value,
    min_size=1,
    max_size=5,
)

namelist_data_strategy = st.dictionaries(
    keys=st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=20),
    values=_namelist_block,
    min_size=1,
    max_size=3,
)

ascii_data_strategy = st.builds(
    lambda arr, comment: {"values": arr, "comment": comment},
    arr=st.lists(
        st.floats(
            min_value=-1e4,
            max_value=1e4,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
            width=32,
        ),
        min_size=2,
        max_size=10,
    ).map(lambda xs: numpy.array(xs, dtype=numpy.float64).reshape(1, -1)),
    comment=st.text(
        alphabet=string.ascii_letters + string.digits + " _-",
        min_size=1,
        max_size=50,
    ),
)

netcdf_data_strategy = st.builds(
    lambda time, var1, var2: xarray.Dataset(
        data_vars={
            "var1": (["time"], var1),
            "var2": (["time"], var2),
        },
        coords={"time": time},
    ),
    time=st.datetimes(
        min_value=datetime.datetime(2000, 1, 1),
        max_value=datetime.datetime(2000, 12, 31, 20, 0, 0),
    ).map(lambda dt: numpy.array([dt + datetime.timedelta(hours=i) for i in range(5)])),
    var1=st.lists(
        st.floats(
            min_value=-100,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
        ),
        min_size=5,
        max_size=5,
    ).map(lambda xs: numpy.array(xs)),
    var2=st.lists(
        st.floats(
            min_value=-100,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
            allow_subnormal=False,
        ),
        min_size=5,
        max_size=5,
    ).map(lambda xs: numpy.array(xs)),
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_namelist_dict() -> dict:
    return {
        "jules_output_profile": {
            "profile_name": "test",
            "output_period": 1800,
            "nvars": 22,
            "output_main_run": True,
            "var": ["pstar", "tl1", "tstar"],
        },
        "jules_time": {
            "timestep_len": 1800,
            "main_run_start": "1996-12-31 23:00:00",
        },
    }


@pytest.fixture
def sample_ascii_data() -> dict:
    return {
        "values": numpy.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
        "comment": "# Initial conditions\n# Generated for testing",
    }


@pytest.fixture
def sample_netcdf_data() -> xarray.Dataset:
    return xarray.Dataset(
        data_vars={
            "sw_down": (["time"], numpy.array([0.0, 100.0, 200.0, 150.0, 0.0])),
            "air_temp": (
                ["time"],
                numpy.array([260.0, 265.0, 270.0, 268.0, 262.0]),
            ),
        },
        coords={
            "time": numpy.array(
                [
                    "1997-01-01T00:00",
                    "1997-01-01T06:00",
                    "1997-01-01T12:00",
                    "1997-01-01T18:00",
                    "1997-01-02T00:00",
                ],
                dtype="datetime64[ns]",
            ),
        },
    )


@pytest.fixture
def namelist_dir(tmp_path: Path, sample_namelist_dict: dict) -> Path:
    nml_dir = tmp_path / "namelists"
    nml_dir.mkdir()
    config = NamelistConfig()
    for node in config.nodes():
        f90nml.write(sample_namelist_dict, nml_dir / node.path)
    return nml_dir


def _write_ascii_file(directory: Path, filename: str, data: dict) -> None:
    handler = AsciiFileHandler()
    with chdir(directory):
        handler.write(filename, data)


def _write_netcdf_file(directory: Path, filename: str, data: xarray.Dataset) -> None:
    handler = NetcdfFileHandler()
    with chdir(directory):
        handler.write(filename, data)


@pytest.fixture
def inputs_dir_ascii(tmp_path: Path, sample_ascii_data: dict) -> Path:
    inp_dir = tmp_path / "inputs"
    inp_dir.mkdir()
    _write_ascii_file(inp_dir, "initial_conditions.dat", sample_ascii_data)
    _write_ascii_file(inp_dir, "tile_fractions.dat", sample_ascii_data)
    _write_ascii_file(inp_dir, "driving_data.dat", sample_ascii_data)
    return inp_dir


@pytest.fixture
def inputs_dir_netcdf(
    tmp_path: Path,
    sample_ascii_data: dict,
    sample_netcdf_data: xarray.Dataset,
) -> Path:
    inp_dir = tmp_path / "inputs"
    inp_dir.mkdir()
    _write_ascii_file(inp_dir, "initial_conditions.dat", sample_ascii_data)
    _write_ascii_file(inp_dir, "tile_fractions.dat", sample_ascii_data)
    _write_netcdf_file(inp_dir, "driving_data.nc", sample_netcdf_data)
    return inp_dir


# ---------------------------------------------------------------------------
# NamelistFileHandler tests
# ---------------------------------------------------------------------------


class TestNamelistFileHandler:
    def test_read_single_block(self, tmp_path):
        nml_path = tmp_path / "test.nml"
        f90nml.write({"block": {"a": 1, "b": 2.5}}, nml_path)
        handler = NamelistFileHandler()
        result = handler.read(nml_path)
        assert "block" in result
        assert result["block"]["a"] == 1
        assert result["block"]["b"] == 2.5

    def test_read_multiple_blocks(self, tmp_path):
        nml_path = tmp_path / "test.nml"
        data = {"block_a": {"x": 10}, "block_b": {"y": "hello"}}
        f90nml.write(data, nml_path)
        handler = NamelistFileHandler()
        result = handler.read(nml_path)
        assert "block_a" in result
        assert "block_b" in result
        assert result["block_a"]["x"] == 10
        assert result["block_b"]["y"] == "hello"

    def test_read_returns_dict_not_ordereddict(self, tmp_path):
        nml_path = tmp_path / "test.nml"
        f90nml.write({"block": {"a": 1}}, nml_path)
        handler = NamelistFileHandler()
        result = handler.read(nml_path)
        assert type(result) is dict
        assert type(result["block"]) is dict

    def test_write_creates_file(self, tmp_path):
        nml_path = tmp_path / "output.nml"
        handler = NamelistFileHandler()
        handler.write(nml_path, {"section": {"param": 42}})
        assert nml_path.exists()

    def test_write_without_overwrite_fails_if_exists(self, tmp_path):
        nml_path = tmp_path / "output.nml"
        data = {"section": {"param": 42}}
        handler = NamelistFileHandler()
        handler.write(nml_path, data)
        with pytest.raises(OSError, match="already exists"):
            handler.write(nml_path, data)

    def test_write_with_overwrite_ok(self, tmp_path):
        nml_path = tmp_path / "output.nml"
        handler = NamelistFileHandler()
        handler.write(nml_path, {"section": {"param": 1}})
        handler.write(nml_path, {"section": {"param": 2}}, overwrite_ok=True)
        result = handler.read(nml_path)
        assert result["section"]["param"] == 2

    def test_round_trip(self, tmp_path, sample_namelist_dict):
        nml_path = tmp_path / "roundtrip.nml"
        handler = NamelistFileHandler()
        handler.write(nml_path, sample_namelist_dict)
        result = handler.read(nml_path)
        assert result == sample_namelist_dict

    def test_write_with_list_values(self, tmp_path):
        nml_path = tmp_path / "list.nml"
        data = {"block": {"arr": [1, 2, 3]}}
        handler = NamelistFileHandler()
        handler.write(nml_path, data)
        result = handler.read(nml_path)
        assert result["block"]["arr"] == [1, 2, 3]

    def test_write_with_boolean_values(self, tmp_path):
        nml_path = tmp_path / "bool.nml"
        data = {"block": {"flag": True, "other": False}}
        handler = NamelistFileHandler()
        handler.write(nml_path, data)
        result = handler.read(nml_path)
        assert result["block"]["flag"] is True
        assert result["block"]["other"] is False

    def test_write_with_string_values(self, tmp_path):
        nml_path = tmp_path / "str.nml"
        data = {"block": {"name": "test_value"}}
        handler = NamelistFileHandler()
        handler.write(nml_path, data)
        result = handler.read(nml_path)
        assert result["block"]["name"] == "test_value"

    @given(namelist_data_strategy)
    @settings(
        max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_hypothesis_round_trip(self, tmp_path, data):
        handler = NamelistFileHandler()
        nml_path = tmp_path / "hypothesis.nml"
        if nml_path.exists():
            nml_path.unlink()
        handler.write(nml_path, data, overwrite_ok=True)
        result = handler.read(nml_path)
        for block_name in data:
            lower_name = block_name.lower()
            assert lower_name in result
            for key in data[block_name]:
                assert key in result[lower_name]

    def test_read_with_pathlike(self, tmp_path):
        nml_path = tmp_path / "test.nml"
        f90nml.write({"block": {"a": 1}}, nml_path)
        handler = NamelistFileHandler()
        result = handler.read(Path(nml_path))
        assert result["block"]["a"] == 1

    def test_write_with_pathlike(self, tmp_path):
        nml_path = tmp_path / "test.nml"
        handler = NamelistFileHandler()
        handler.write(Path(nml_path), {"block": {"a": 1}})
        assert nml_path.exists()


# ---------------------------------------------------------------------------
# NamelistConfig tests
# ---------------------------------------------------------------------------


class TestNamelistConfig:
    def test_instantiation_no_args(self):
        config = NamelistConfig()
        assert config is not None

    def test_has_all_29_namelist_fields(self):
        config = NamelistConfig()
        expected_fields = [
            "ancillaries",
            "crop_params",
            "drive",
            "fire",
            "imogen",
            "initial_conditions",
            "jules_deposition",
            "jules_hydrology",
            "jules_irrig",
            "jules_prnt_control",
            "jules_radiation",
            "jules_rivers",
            "jules_snow",
            "jules_soil_biogeochem",
            "jules_soil",
            "jules_surface",
            "jules_surface_types",
            "jules_vegetation",
            "jules_water_resources",
            "model_environment",
            "model_grid",
            "nveg_params",
            "output",
            "pft_params",
            "prescribed_data",
            "science_fixes",
            "timesteps",
            "triffid_params",
            "urban",
        ]
        node_paths = {str(node.path) for node in config.nodes()}
        for field in expected_fields:
            assert f"{field}.nml" in node_paths

    def test_node_count(self):
        config = NamelistConfig()
        assert len(list(config.nodes())) == 29

    def test_read_all_namelists(self, namelist_dir):
        config = NamelistConfig()
        result = config.read(namelist_dir)
        assert "output" in result
        assert "timesteps" in result

    def test_write_all_namelists(self, namelist_dir, tmp_path):
        config = NamelistConfig()
        data = config.read(namelist_dir)
        out_dir = tmp_path / "output_namelists"
        out_dir.mkdir()
        config.write(out_dir, data, overwrite_ok=True)
        for node in config.nodes():
            assert (out_dir / node.path).exists()

    def test_round_trip(self, namelist_dir, tmp_path):
        config = NamelistConfig()
        original = config.read(namelist_dir)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        config.write(out_dir, original, overwrite_ok=True)
        reread = config.read(out_dir)
        assert reread == original

    def test_read_raises_on_missing_files(self, tmp_path):
        empty_dir = tmp_path / "empty_namelists"
        empty_dir.mkdir()
        config = NamelistConfig()
        with pytest.raises(FileNotFoundError):
            config.read(empty_dir)


# ---------------------------------------------------------------------------
# AsciiFileHandler tests
# ---------------------------------------------------------------------------


class TestAsciiFileHandler:
    def test_read_2d_data_with_comments(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text(
            "# Header line 1\n# Header line 2\n1.0 2.0 3.0\n4.0 5.0 6.0\n"
        )
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.dat")
        assert result["comment"] == "# Header line 1\n# Header line 2"
        expected = numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        numpy.testing.assert_array_equal(result["values"], expected)

    def test_read_1d_data_reshaped_to_2d(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text("1.0 2.0 3.0\n")
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.dat")
        assert result["values"].shape == (1, 3)
        numpy.testing.assert_array_equal(result["values"], [[1.0, 2.0, 3.0]])

    def test_read_no_comments(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text("1.0 2.0\n3.0 4.0\n")
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.dat")
        assert result["comment"] == ""

    def test_read_with_exclamation_comments(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text("! Fortran-style comment\n1.0 2.0\n")
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.dat")
        assert result["comment"] == "! Fortran-style comment"

    def test_write_creates_file(self, tmp_path):
        handler = AsciiFileHandler()
        data = {
            "values": numpy.array([[1.0, 2.0], [3.0, 4.0]]),
            "comment": "# test",
        }
        with chdir(tmp_path):
            handler.write("output.dat", data)
        assert (tmp_path / "output.dat").exists()

    def test_write_format(self, tmp_path):
        handler = AsciiFileHandler()
        data = {"values": numpy.array([[1.0, 2.0]]), "comment": "# header"}
        with chdir(tmp_path):
            handler.write("output.dat", data)
        content = (tmp_path / "output.dat").read_text()
        assert "# header" in content
        assert "1.00000" in content
        assert "2.00000" in content

    def test_write_overwrites_existing_file(self, tmp_path):
        handler = AsciiFileHandler()
        data = {"values": numpy.array([[1.0, 2.0, 3.0]]), "comment": "# first"}
        with chdir(tmp_path):
            handler.write("output.dat", data)
            data2 = {"values": numpy.array([[4.0, 5.0, 6.0]]), "comment": "# second"}
            handler.write("output.dat", data2)
            result = handler.read("output.dat")
        numpy.testing.assert_array_equal(result["values"], [[4.0, 5.0, 6.0]])
        assert "second" in result["comment"]

    def test_round_trip_2d(self, tmp_path, sample_ascii_data):
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            handler.write("roundtrip.dat", sample_ascii_data)
            result = handler.read("roundtrip.dat")
        numpy.testing.assert_array_equal(result["values"], sample_ascii_data["values"])
        assert "Initial conditions" in result["comment"]
        assert "Generated for testing" in result["comment"]

    def test_round_trip_1d_reshaped(self, tmp_path):
        handler = AsciiFileHandler()
        original = {
            "values": numpy.array([[1.0, 2.0, 3.0]]),
            "comment": "# single row",
        }
        with chdir(tmp_path):
            handler.write("roundtrip.dat", original)
            result = handler.read("roundtrip.dat")
        numpy.testing.assert_array_equal(result["values"], original["values"])

    def test_read_returns_typed_dict(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text("1.0 2.0\n")
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.dat")
        assert "values" in result
        assert "comment" in result
        assert isinstance(result["values"], numpy.ndarray)
        assert isinstance(result["comment"], str)

    @given(ascii_data_strategy)
    @settings(
        max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_hypothesis_round_trip(self, tmp_path, data):
        handler = AsciiFileHandler()
        fname = "hypothesis.dat"
        fpath = tmp_path / fname
        if fpath.exists():
            fpath.unlink()
        with chdir(tmp_path):
            handler.write(fname, data)
            result = handler.read(fname)
        numpy.testing.assert_array_almost_equal(
            result["values"], data["values"], decimal=4
        )

    def test_write_absolute_path_skipped(self):
        handler = AsciiFileHandler()
        data = {"values": numpy.array([[1.0]]), "comment": "# test"}
        result = handler.write("/absolute/path.dat", data)
        assert result is None

    def test_read_missing_file_handled_gracefully(self, tmp_path):
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read("nonexistent.dat")
        assert result is MISSING

    def test_write_with_pathlike(self, tmp_path):
        handler = AsciiFileHandler()
        data = {"values": numpy.array([[1.0]]), "comment": ""}
        with chdir(tmp_path):
            handler.write(Path("output.dat"), data)
        assert (tmp_path / "output.dat").exists()

    def test_read_with_pathlike(self, tmp_path):
        txt_path = tmp_path / "data.dat"
        txt_path.write_text("1.0 2.0\n")
        handler = AsciiFileHandler()
        with chdir(tmp_path):
            result = handler.read(Path("data.dat"))
        assert result["values"].shape == (1, 2)

    def test_empty_comment_string(self, tmp_path):
        handler = AsciiFileHandler()
        data = {"values": numpy.array([[1.0, 2.0]]), "comment": ""}
        with chdir(tmp_path):
            handler.write("data.dat", data)
            result = handler.read("data.dat")
        numpy.testing.assert_array_equal(result["values"], [[1.0, 2.0]])

    def test_multiline_comment_round_trip(self, tmp_path):
        handler = AsciiFileHandler()
        comment = "# Line 1\n# Line 2\n# Line 3"
        data = {"values": numpy.array([[1.0, 2.0, 3.0]]), "comment": comment}
        with chdir(tmp_path):
            handler.write("data.dat", data)
            result = handler.read("data.dat")
        numpy.testing.assert_array_equal(result["values"], [[1.0, 2.0, 3.0]])
        assert "Line 1" in result["comment"]
        assert "Line 2" in result["comment"]
        assert "Line 3" in result["comment"]


# ---------------------------------------------------------------------------
# NetcdfFileHandler tests
# ---------------------------------------------------------------------------


class TestNetcdfFileHandler:
    def test_read_netcdf(self, tmp_path, sample_netcdf_data):
        nc_path = tmp_path / "data.nc"
        sample_netcdf_data.to_netcdf(nc_path)
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.nc")
        assert isinstance(result, xarray.Dataset)
        assert "sw_down" in result.data_vars
        assert "air_temp" in result.data_vars
        assert "time" in result.coords

    def test_write_netcdf(self, tmp_path, sample_netcdf_data):
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write("output.nc", sample_netcdf_data)
        assert (tmp_path / "output.nc").exists()

    def test_write_without_overwrite_fails_if_exists(
        self, tmp_path, sample_netcdf_data
    ):
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write("output.nc", sample_netcdf_data)
            with pytest.raises(FileExistsError, match="already a file"):
                handler.write("output.nc", sample_netcdf_data)

    def test_write_with_overwrite_ok(self, tmp_path):
        handler = NetcdfFileHandler()
        ds1 = xarray.Dataset({"var": (["x"], [1.0, 2.0])})
        ds2 = xarray.Dataset({"var": (["x"], [3.0, 4.0])})
        with chdir(tmp_path):
            handler.write("output.nc", ds1)
            handler.write("output.nc", ds2, overwrite_ok=True)
            result = handler.read("output.nc")
        numpy.testing.assert_array_equal(result["var"].values, [3.0, 4.0])

    def test_round_trip(self, tmp_path, sample_netcdf_data):
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write("roundtrip.nc", sample_netcdf_data)
            result = handler.read("roundtrip.nc")
        xarray.testing.assert_identical(result, sample_netcdf_data)

    def test_read_returns_xarray_dataset(self, tmp_path, sample_netcdf_data):
        nc_path = tmp_path / "data.nc"
        sample_netcdf_data.to_netcdf(nc_path)
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            result = handler.read("data.nc")
        assert isinstance(result, xarray.Dataset)

    def test_read_with_pathlike(self, tmp_path, sample_netcdf_data):
        nc_path = tmp_path / "data.nc"
        sample_netcdf_data.to_netcdf(nc_path)
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            result = handler.read(Path("data.nc"))
        assert isinstance(result, xarray.Dataset)

    def test_write_with_pathlike(self, tmp_path, sample_netcdf_data):
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write(Path("output.nc"), sample_netcdf_data)
        assert (tmp_path / "output.nc").exists()

    @given(netcdf_data_strategy)
    @settings(
        max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_hypothesis_round_trip(self, tmp_path, dataset):
        handler = NetcdfFileHandler()
        fname = "hypothesis.nc"
        fpath = tmp_path / fname
        if fpath.exists():
            fpath.unlink()
        with chdir(tmp_path):
            handler.write(fname, dataset)
            result = handler.read(fname)
        xarray.testing.assert_identical(result, dataset)

    def test_read_absolute_path_skipped(self):
        handler = NetcdfFileHandler()
        result = handler.read("/absolute/path.nc")
        assert result is MISSING

    def test_write_absolute_path_skipped(self):
        handler = NetcdfFileHandler()
        ds = xarray.Dataset({"var": (["x"], [1.0])})
        result = handler.write("/absolute/path.nc", ds)
        assert result is None

    def test_read_missing_file_handled_gracefully(self, tmp_path):
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            result = handler.read("nonexistent.nc")
        assert result is MISSING

    def test_dataset_with_multiple_variables(self, tmp_path):
        ds = xarray.Dataset(
            {
                "temp": (["time", "lat"], numpy.random.rand(5, 3)),
                "precip": (["time"], numpy.random.rand(5)),
            },
            coords={
                "time": numpy.arange(5),
                "lat": numpy.array([10.0, 20.0, 30.0]),
            },
        )
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write("multi.nc", ds)
            result = handler.read("multi.nc")
        assert "temp" in result.data_vars
        assert "precip" in result.data_vars
        assert result["temp"].shape == (5, 3)

    def test_dataset_with_attributes(self, tmp_path):
        ds = xarray.Dataset(
            {"var": (["x"], [1.0, 2.0])},
            attrs={"title": "test dataset", "version": "1.0"},
        )
        handler = NetcdfFileHandler()
        with chdir(tmp_path):
            handler.write("attrs.nc", ds)
            result = handler.read("attrs.nc")
        assert result.attrs.get("title") == "test dataset"


# ---------------------------------------------------------------------------
# InputFilesConfig tests
# ---------------------------------------------------------------------------


class TestInputFilesConfig:
    def test_instantiation(self):
        config = InputFilesConfig(
            initial_conditions="init.dat",
            tile_fractions="tiles.dat",
            driving_data="driving.nc",
        )
        assert config is not None

    def test_read_ascii_driving_data(self, inputs_dir_ascii):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.dat",
        )
        result = config.read(inputs_dir_ascii)
        assert "initial_conditions" in result
        assert "tile_fractions" in result
        assert "driving_data" in result
        assert "values" in result["initial_conditions"]
        assert "values" in result["tile_fractions"]
        assert "values" in result["driving_data"]

    def test_read_netcdf_driving_data(self, inputs_dir_netcdf):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.nc",
        )
        result = config.read(inputs_dir_netcdf)
        assert "initial_conditions" in result
        assert "tile_fractions" in result
        assert "driving_data" in result
        assert isinstance(result["driving_data"], xarray.Dataset)

    def test_write_ascii_driving_data(self, inputs_dir_ascii, tmp_path):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.dat",
        )
        data = config.read(inputs_dir_ascii)
        out_dir = tmp_path / "output_inputs"
        out_dir.mkdir()
        config.write(out_dir, data, overwrite_ok=True)
        assert (out_dir / "initial_conditions.dat").exists()
        assert (out_dir / "tile_fractions.dat").exists()
        assert (out_dir / "driving_data.dat").exists()

    def test_write_netcdf_driving_data(self, inputs_dir_netcdf, tmp_path):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.nc",
        )
        data = config.read(inputs_dir_netcdf)
        out_dir = tmp_path / "output_inputs"
        out_dir.mkdir()
        config.write(out_dir, data, overwrite_ok=True)
        assert (out_dir / "initial_conditions.dat").exists()
        assert (out_dir / "tile_fractions.dat").exists()
        assert (out_dir / "driving_data.nc").exists()

    def test_round_trip_ascii_driving(self, inputs_dir_ascii, tmp_path):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.dat",
        )
        original = config.read(inputs_dir_ascii)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        config.write(out_dir, original, overwrite_ok=True)
        reread = config.read(out_dir)
        for key in ("initial_conditions", "tile_fractions", "driving_data"):
            numpy.testing.assert_array_almost_equal(
                reread[key]["values"],
                original[key]["values"],
            )

    def test_round_trip_netcdf_driving(self, inputs_dir_netcdf, tmp_path):
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.nc",
        )
        original = config.read(inputs_dir_netcdf)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        config.write(out_dir, original, overwrite_ok=True)
        reread = config.read(out_dir)
        for key in ("initial_conditions", "tile_fractions"):
            numpy.testing.assert_array_almost_equal(
                reread[key]["values"],
                original[key]["values"],
            )
        xarray.testing.assert_identical(
            reread["driving_data"],
            original["driving_data"],
        )

    def test_missing_files_handled_gracefully(self, tmp_path):
        empty_dir = tmp_path / "empty_inputs"
        empty_dir.mkdir()
        config = InputFilesConfig(
            initial_conditions="initial_conditions.dat",
            tile_fractions="tile_fractions.dat",
            driving_data="driving_data.nc",
        )
        result = config.read(empty_dir)
        for key in ("initial_conditions", "tile_fractions", "driving_data"):
            assert result[key] is MISSING


# ---------------------------------------------------------------------------
# JulesConfig tests
# ---------------------------------------------------------------------------


class TestJulesConfig:
    def test_instantiation(self):
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        assert config is not None

    def test_namelists_field_is_fixed(self):
        namelist_config = NamelistConfig()
        assert len(list(namelist_config.nodes())) == 29

    def _setup_combined_config_dir(self, tmp_path, namelist_dir, inputs_dir):
        config_dir = tmp_path / "jules_config"
        config_dir.mkdir()
        (config_dir / "namelists").mkdir()
        for nml in namelist_dir.iterdir():
            shutil.copy2(nml, config_dir / "namelists" / nml.name)
        (config_dir / "inputs").mkdir()
        for inp in inputs_dir.iterdir():
            shutil.copy2(inp, config_dir / "inputs" / inp.name)
        return config_dir

    def test_read_full_config_ascii_driving(
        self, namelist_dir, inputs_dir_ascii, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_ascii
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.dat",
                ),
            },
        )
        result = config.read(config_dir)
        assert "namelists" in result
        assert "inputs" in result
        assert "output" in result["namelists"]
        assert "initial_conditions" in result["inputs"]

    def test_read_full_config_netcdf_driving(
        self, namelist_dir, inputs_dir_netcdf, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_netcdf
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        result = config.read(config_dir)
        assert "namelists" in result
        assert "inputs" in result
        assert isinstance(result["inputs"]["driving_data"], xarray.Dataset)

    def test_write_full_config_ascii_driving(
        self, namelist_dir, inputs_dir_ascii, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_ascii
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.dat",
                ),
            },
        )
        data = config.read(config_dir)
        out_dir = tmp_path / "jules_output"
        config.write(out_dir, data, overwrite_ok=True)
        assert (out_dir / "namelists").exists()
        assert (out_dir / "inputs").exists()
        for nml in NamelistConfig().nodes():
            assert (out_dir / "namelists" / nml.path).exists()

    def test_write_full_config_netcdf_driving(
        self, namelist_dir, inputs_dir_netcdf, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_netcdf
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        data = config.read(config_dir)
        out_dir = tmp_path / "jules_output"
        config.write(out_dir, data, overwrite_ok=True)
        assert (out_dir / "namelists").exists()
        assert (out_dir / "inputs").exists()
        assert (out_dir / "inputs" / "driving_data.nc").exists()

    def test_round_trip_full_config_ascii(
        self, namelist_dir, inputs_dir_ascii, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_ascii
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.dat",
                ),
            },
        )
        original = config.read(config_dir)
        out_dir = tmp_path / "jules_output"
        config.write(out_dir, original, overwrite_ok=True)
        reread = config.read(out_dir)
        for key in original["namelists"]:
            assert key in reread["namelists"]
        for key in ("initial_conditions", "tile_fractions", "driving_data"):
            numpy.testing.assert_array_almost_equal(
                reread["inputs"][key]["values"],
                original["inputs"][key]["values"],
            )

    def test_round_trip_full_config_netcdf(
        self, namelist_dir, inputs_dir_netcdf, tmp_path
    ):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_netcdf
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        original = config.read(config_dir)
        out_dir = tmp_path / "jules_output"
        config.write(out_dir, original, overwrite_ok=True)
        reread = config.read(out_dir)
        for key in original["namelists"]:
            assert key in reread["namelists"]
        for key in ("initial_conditions", "tile_fractions"):
            numpy.testing.assert_array_almost_equal(
                reread["inputs"][key]["values"],
                original["inputs"][key]["values"],
            )
        xarray.testing.assert_identical(
            reread["inputs"]["driving_data"],
            original["inputs"]["driving_data"],
        )

    def test_modify_and_write(self, namelist_dir, inputs_dir_netcdf, tmp_path):
        config_dir = self._setup_combined_config_dir(
            tmp_path, namelist_dir, inputs_dir_netcdf
        )
        config = JulesConfig(
            inputs={
                "path": "inputs",
                "handler": lambda: InputFilesConfig(
                    initial_conditions="initial_conditions.dat",
                    tile_fractions="tile_fractions.dat",
                    driving_data="driving_data.nc",
                ),
            },
        )
        data = config.read(config_dir)
        data["namelists"]["output"]["jules_output_profile"]["output_period"] = 3600
        out_dir = tmp_path / "jules_output"
        config.write(out_dir, data, overwrite_ok=True)
        reread = config.read(out_dir)
        assert (
            reread["namelists"]["output"]["jules_output_profile"]["output_period"]
            == 3600
        )


# ---------------------------------------------------------------------------
# Module-level tests
# ---------------------------------------------------------------------------


class TestModuleExports:
    def test_all_exports(self):
        from julesconf import config

        expected = {
            "AsciiFileHandler",
            "InputFilesConfig",
            "JulesConfig",
            "NamelistConfig",
            "NamelistFileHandler",
            "NetcdfFileHandler",
        }
        assert set(config.__all__) == expected

    def test_ascii_handler_module_preserved(self):
        assert AsciiFileHandler.__module__ == "julesconf.config"

    def test_netcdf_handler_module_preserved(self):
        assert NetcdfFileHandler.__module__ == "julesconf.config"
