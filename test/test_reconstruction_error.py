"""TwoPhaseFlow's ``reconstructionError``: the per-cell errors and their norms."""

from __future__ import annotations

import numpy as np

from neofoam_tutorials.reconstruction_error import ReconstructionError, sample_errors
from neofoam_tutorials.shapes import Cylinder


def test_sample_errors_of_tilted_and_shifted_planes() -> None:
    circle = Cylinder(origin=(1.0, 0.0, 1.0), radius=0.5, direction=(0.0, 1.0, 0.0))
    theta = np.linspace(0.0, 2.0 * np.pi, 7, endpoint=False)
    radial = np.column_stack([np.cos(theta), np.zeros_like(theta), np.sin(theta)])
    tilt, shift = 1e-3, 2e-4
    rotated = np.cos(tilt) * -radial + np.sin(tilt) * np.cross(radial, [0.0, 1.0, 0.0])
    centre = np.array(circle.origin) + (0.5 + shift) * radial
    # a zero normal marks a cell without interface; its centre is never looked at
    normal_error, centre_error = sample_errors(
        circle, np.vstack([centre, [0.0, 0.0, 0.0]]), np.vstack([3.0 * rotated, [0, 0, 0]])
    )

    np.testing.assert_allclose(normal_error, 1.0 - np.cos(tilt), rtol=1e-8)
    np.testing.assert_allclose(centre_error, shift, rtol=1e-10)


def test_error_norms_aggregate_like_calcError() -> None:
    errors = ReconstructionError()
    errors.add(np.array([1.0, 3.0]), np.array([0.5, 0.5]))
    errors.add(np.array([2.0]), np.array([4.0, 0.0]))

    assert errors.norms == {"LNormalInf": 3.0, "LNormal1": 2.0, "LCentreInf": 4.0, "LCentre1": 1.25}
