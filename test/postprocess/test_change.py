"""The ``change`` postProcess node on a host dataset."""

from __future__ import annotations

import numpy as np
from neofoam.postprocess import InternalDataSet

from neofoam_tutorials.postprocess._host import HostCells
from neofoam_tutorials.postprocess.change import Change


def _cells(z: np.ndarray, values: np.ndarray) -> InternalDataSet:
    positions = np.column_stack([np.zeros_like(z), np.zeros_like(z), z])
    return InternalDataSet(name="p", field=values, geometry=HostCells(positions, np.ones(len(z))))


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
