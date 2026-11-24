"""The ``hydrostaticError`` postProcess node on a host dataset."""

from __future__ import annotations

import numpy as np
from neofoam.postprocess import InternalDataSet

from neofoam_tutorials.postprocess._host import HostCells
from neofoam_tutorials.postprocess.hydrostatic import HydrostaticError


def _cells(z: np.ndarray, values: np.ndarray) -> InternalDataSet:
    positions = np.column_stack([np.zeros_like(z), np.zeros_like(z), z])
    return InternalDataSet(name="p", field=values, geometry=HostCells(positions, np.ones(len(z))))


def test_hydrostatic_error_is_zero_for_the_hydrostatic_pressure() -> None:
    z = np.linspace(0.05, 0.95, 10)
    node = HydrostaticError(
        rho_heavy=1000, rho_light=1, g=(0, 0, -10), origin=(0, 0, 0.5), normal=(0, 0, -1)
    )
    # water below z = 0.5: p = 1 * (-10 * 0.5) + 1000 * (-10) * (z - 0.5); air above: -10 z
    exact = np.where(z < 0.5, -5.0 - 10000.0 * (z - 0.5), -10.0 * z)

    assert np.allclose(node.compute(_cells(z, exact)).field, 0.0, atol=1e-15)
    error = node.compute(_cells(z, exact + 1.0)).field
    assert np.allclose(error, 1.0 / np.ptp(exact))
