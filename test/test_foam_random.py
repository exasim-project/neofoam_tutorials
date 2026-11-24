"""The circle case's interface centres: TwoPhaseFlow's ``reconstructInterface`` sequence."""

from __future__ import annotations

import numpy as np

from neofoam_tutorials.foam_random import centres

# reconstructInterface's log ("centre (x y z)", writePrecision 17) of the circle case
LOGGED_CENTRES = np.array(
    [
        [1.0878855217857544, 0, 0.97443629964981937],
        [1.0972591172088473, 0, 0.93582405910630817],
        [1.0257658133431258, 0, 0.91099023637235876],
        [0.92557657194070997, 0, 0.94332249869011919],
        [0.92464754400267557, 0, 1.0847629646164472],
        [0.92385741347478489, 0, 1.051489085363505],
        [1.0469269583891947, 0, 1.0925552821071121],
        [1.0750231410959894, 0, 1.0178913502986584],
        [0.92728898690711803, 0, 1.072973156041406],
        [0.9180053060437019, 0, 0.96839075325581381],
    ]
)


def test_centres_are_reconstructInterface_sequence() -> None:
    np.testing.assert_array_equal(centres(np.array([1.01, 0.0, 1.01]), 10), LOGGED_CENTRES)
