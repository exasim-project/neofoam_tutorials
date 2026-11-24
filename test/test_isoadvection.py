"""The exact shape the isoAdvection reference's errors compare against."""

from __future__ import annotations

import numpy as np

from neofoam_tutorials.isoadvection import RUNS, exact_shape, velocities


def test_rotation_moves_the_disc_by_the_angle() -> None:
    spec = velocities(RUNS["curvature2D"])["rotation"]
    shape = exact_shape(RUNS["curvature2D"], "rotation", None, np.pi / float(spec["omega"]))
    # half a turn mirrors the centre at the rotation origin (x-z plane)
    origin = np.asarray(spec["origin"], dtype=float)
    centre = 2 * origin - np.array([1.01, 0.0, 1.01])
    np.testing.assert_allclose(shape.origin, centre, atol=1e-14)
