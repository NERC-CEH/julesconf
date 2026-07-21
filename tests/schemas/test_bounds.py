"""Spot-check tests for field bounds (plain types; sentinel only on albsnf_nvg_io)."""

import pytest
from pydantic import ValidationError

from julesconf.schemas.nveg_params import JulesNvegparm
from julesconf.schemas.pft_params import JulesPftparm
from julesconf.schemas.triffid_params import JulesTriffid


@pytest.mark.parametrize(
    ("model_cls", "field_name", "good", "bad"),
    [
        # SentinelOrFraction — only albsnf_nvg_io keeps sentinel
        (JulesNvegparm, "albsnf_nvg_io", [-1.0, 0.0, 1.0], [-2.0, 1.5]),
        # Fraction
        (JulesPftparm, "albsnf_max_io", [0.0, 0.5], [-1.0, -0.5, 1.1]),
        (JulesPftparm, "emis_pft_io", [0.0, 0.98], [-1.0, -0.01, 1.01]),
        # NonNegFloat
        (JulesPftparm, "canht_ft_io", [0.0, 19.0], [-2.0, -1.0, -0.1]),
        (JulesPftparm, "catch0_io", [0.0, 0.5], [-1.0, -0.5]),
        # ZeroOne
        (JulesPftparm, "c3_io", [0, 1], [-1, -2, 2]),
        (JulesPftparm, "orient_io", [0, 1], [-1, 2]),
        # crop_io — plain Field(ge=0, le=3), no sentinel
        (JulesTriffid, "crop_io", [0, 1, 2, 3], [-1, -2, 4]),
    ],
)
def test_bounds(model_cls, field_name, good, bad):
    for val in good:
        model_cls.model_validate({field_name: [val]})
    for val in bad:
        with pytest.raises(ValidationError, match=field_name):
            model_cls.model_validate({field_name: [val]})
