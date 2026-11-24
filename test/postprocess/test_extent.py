"""The ``phaseExtent`` postProcess node on a host dataset.

Four cells in a row along x; the node's values feed ``max``, so the test checks the
values it hands on: the x of the cells inside the phase, the smallest x elsewhere.
"""

from __future__ import annotations

import numpy as np
from neofoam.postprocess import InternalDataSet

from neofoam_tutorials.postprocess._host import HostCells
from neofoam_tutorials.postprocess.extent import PhaseExtent


def _row(alpha: list[float]) -> InternalDataSet:
    x = np.array([0.5, 1.5, 2.5, 3.5])
    positions = np.column_stack([x, np.zeros(4), np.zeros(4)])
    geometry = HostCells(positions, np.ones(4))
    return InternalDataSet(name="alpha1", field=np.array(alpha), geometry=geometry)


def test_phase_extent_is_the_coordinate_inside_the_phase() -> None:
    node = PhaseExtent(direction=(1, 0, 0))

    extent = node.compute(_row([1.0, 0.9, 0.4, 0.0])).field

    np.testing.assert_array_equal(extent, [0.5, 1.5, 0.5, 0.5])
