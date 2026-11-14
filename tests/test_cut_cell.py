"""The cut-cell volume fraction on a single unit cube, against hand-computed volumes."""

from __future__ import annotations

import numpy as np
import pytest

from neofoam_verification.cut_cell import exact_alpha
from neofoam_verification.foam import PolyMesh

# one hex cell, OpenFOAM point and face ordering (all faces boundary faces)
POINTS = np.array(
    [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
    dtype=float,
)
FACES = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [3, 7, 6, 2], [0, 4, 7, 3], [1, 2, 6, 5]]


@pytest.fixture
def cube() -> PolyMesh:
    return PolyMesh(
        points=POINTS,
        faces=[np.array(f) for f in FACES],
        owner=np.zeros(6, dtype=np.int64),
        neighbour=np.zeros(0, dtype=np.int64),
    )


@pytest.mark.parametrize(
    "plane_value, expected",
    [
        # f = 0.3 - x: fluid below x = 0.3
        (lambda p: 0.3 - p[:, 0], 0.3),
        # f = 1 - x - y - z: the corner tetrahedron, volume 1/6
        (lambda p: 1.0 - p.sum(axis=1), 1.0 / 6.0),
        # f = 0.5 - x + 0.4 (y - 0.5): a slanted cut through the middle
        (lambda p: 0.5 - p[:, 0] + 0.4 * (p[:, 1] - 0.5), 0.5),
        # fully inside / outside
        (lambda p: 1.0 + 0.0 * p[:, 0], 1.0),
        (lambda p: -1.0 + 0.0 * p[:, 0], 0.0),
    ],
)
def test_cut_cell_volume_fraction_of_a_plane(cube: PolyMesh, plane_value, expected) -> None:  # type: ignore[no-untyped-def]
    alpha = exact_alpha(cube, plane_value(cube.points))
    np.testing.assert_allclose(alpha, [expected], rtol=1e-14)
