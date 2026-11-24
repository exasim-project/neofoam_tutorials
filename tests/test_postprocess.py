"""The benchmarks' NeoFOAM postProcess nodes on host datasets, and the error columns
collect derives from the volume-fraction tables."""

from __future__ import annotations

import numpy as np
import pandas as pd
from neofoam.postprocess import InternalDataSet

from neofoam_tutorials.metrics import bound_error, mass_error, table_errors
from neofoam_tutorials.postprocess._host import HostCells
from neofoam_tutorials.postprocess.change import Change
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


def test_change_masks_the_first_evaluation_then_takes_the_largest_component() -> None:
    z = np.array([0.25, 0.75])
    velocity = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
    node = Change()

    first = node.compute(_cells(z, velocity))
    second = node.compute(_cells(z, velocity + [[0.0, -0.5, 0.0], [0.1, 0.0, 0.0]]))

    # every cell masked out: max writes -GREAT (collect's NaN)
    assert first.mask.tolist() == [0, 0]
    assert second.mask is None
    assert second.field.tolist() == [0.5, 0.1]


def test_table_errors_are_volume_fraction_errors_mass_and_bound_errors() -> None:
    alpha, volumes = np.array([-1e-3, 0.5, 1.0 + 2e-3]), np.array([1.0, 2.0, 3.0])
    history = pd.DataFrame(
        {"mass": [alpha @ volumes], "mass0": [3.5], "alpha_min": [alpha.min()]}
    ).assign(alpha_max=alpha.max())

    errors = table_errors(history).iloc[0]

    assert errors["Emass"] == mass_error(alpha, volumes, 3.5)
    assert errors["Ebound"] == bound_error(alpha)
