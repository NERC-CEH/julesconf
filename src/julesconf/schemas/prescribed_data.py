"""Validation schema for `prescribed_data.nml`.

Reference: JULES user guide v7.9,
`jules-lsm.github.io/user_guide/doc/source/namelists/prescribed_data.nml.rst`
"""

from julesconf.schemas._base import NamelistModel

__all__ = [
    "JulesPrescribed",
    "JulesPrescribedDataset",
    "PrescribedDataNamelist",
]


class JulesPrescribed(NamelistModel):
    """`JULES_PRESCRIBED` namelist members."""

    n_datasets: int = 0
    """The number of datasets that will be specified using instances of JULES_PRESCRIBED_DATASET."""


class JulesPrescribedDataset(NamelistModel):
    """`JULES_PRESCRIBED_DATASET` namelist members."""


class PrescribedDataNamelist(NamelistModel):
    """Top-level schema for `prescribed_data.nml`."""

    jules_prescribed: JulesPrescribed = JulesPrescribed()
    jules_prescribed_dataset: JulesPrescribedDataset = JulesPrescribedDataset()
