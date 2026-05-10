"""Validation schema for ``prescribed_data.nml``.

Reference: JULES user guide v7.9,
``jules-lsm.github.io/user_guide/doc/source/namelists/prescribed_data.nml.rst``
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["PrescribedDataNamelist"]


class JulesPrescribed(BaseModel):
    """``JULES_PRESCRIBED`` namelist members."""

    model_config = ConfigDict(extra="ignore")

    n_datasets: int = 0


class JulesPrescribedDataset(BaseModel):
    """``JULES_PRESCRIBED_DATASET`` namelist members."""

    model_config = ConfigDict(extra="ignore")


class PrescribedDataNamelist(BaseModel):
    """Top-level schema for ``prescribed_data.nml``."""

    model_config = ConfigDict(extra="ignore")

    jules_prescribed: JulesPrescribed = JulesPrescribed()
    jules_prescribed_dataset: JulesPrescribedDataset = JulesPrescribedDataset()
