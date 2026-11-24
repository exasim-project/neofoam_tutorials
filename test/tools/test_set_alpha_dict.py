"""The level set of a ``setAlphaFieldDict``, positive inside the shape.

The dicts are the benchmarks' own (read with foamlib, as the tool does); the points
are on the axis, on the surface and outside, so the expected values are the distances.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from foamlib import FoamFile

from neofoam_tutorials.tools.set_alpha_dict import level_set

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"


def test_level_set_of_the_disc_is_the_radius_minus_the_axis_distance() -> None:
    spec = FoamFile(BENCHMARKS / "advection/discUniFlow/case/system/setAlphaFieldDict")
    points = np.array([[0.25, 0.7, 0.25], [0.45, 0.0, 0.25], [0.25, 0.0, 0.75]])

    values = level_set(spec, points)

    np.testing.assert_allclose(values, [0.2, 0.0, -0.3], atol=1e-15, err_msg="discUniFlow")
