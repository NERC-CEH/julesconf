"""Spot-check tests for sentinel-aware bounds added in this PR."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.nveg_params import JulesNvegparm
from julesconf.schemas.pft_params import JulesPftparm
from julesconf.schemas.triffid_params import JulesTriffid


@pytest.mark.parametrize(
    ("model_cls", "field_name", "good", "bad"),
    [
        # SentinelOrFraction
        (JulesNvegparm, "albsnf_nvg_io", [-1.0, 0.0, 1.0], [-2.0, 1.5]),
        (JulesPftparm, "albsnf_max_io", [-1.0, 0.5], [-0.5, 1.1]),
        (JulesPftparm, "emis_pft_io", [-1.0, 0.98], [-0.01, 1.01]),
        # SentinelOrNonNegFloat
        (JulesPftparm, "canht_ft_io", [-1.0, 0.0, 19.0], [-2.0, -0.1]),
        (JulesPftparm, "catch0_io", [-1.0, 0.5], [-0.5]),
        # SentinelOrZeroOne
        (JulesPftparm, "c3_io", [-1, 0, 1], [-2, 2]),
        (JulesPftparm, "orient_io", [-1, 1], [2]),
        # crop_io special range with sentinel
        (JulesTriffid, "crop_io", [-1, 0, 1, 2], [-2, 3]),
    ],
)
def test_bounds(model_cls, field_name, good, bad):
    for val in good:
        model_cls.model_validate({field_name: [val]})
    for val in bad:
        with pytest.raises(ValidationError, match=field_name):
            model_cls.model_validate({field_name: [val]})
