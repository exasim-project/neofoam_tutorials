"""The error columns collect derives from the volume-fraction tables."""

from __future__ import annotations

import numpy as np
import pandas as pd

from neofoam_tutorials.metrics import bound_error, mass_error, table_errors


def test_table_errors_are_volume_fraction_errors_mass_and_bound_errors() -> None:
    alpha, volumes = np.array([-1e-3, 0.5, 1.0 + 2e-3]), np.array([1.0, 2.0, 3.0])
    history = pd.DataFrame(
        {"mass": [alpha @ volumes], "mass0": [3.5], "alpha_min": [alpha.min()]}
    ).assign(alpha_max=alpha.max())

    errors = table_errors(history).iloc[0]

    assert errors["Emass"] == mass_error(alpha, volumes, 3.5)
    assert errors["Ebound"] == bound_error(alpha)
