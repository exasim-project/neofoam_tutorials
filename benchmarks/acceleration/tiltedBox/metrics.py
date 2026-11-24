"""The tilted box's derived columns (``collect.derive``), per write time.

From the case's ``postProcess`` tables (``case/system/postProcess.yaml``: ``maxU`` --
the largest cell ``|U|``, the spurious current; ``p_err_max`` -- the largest ``|p -
p_hydrostatic|`` relative to the hydrostatic pressure range, this repository's
``hydrostaticError`` node; ``magU_integral``, ``p_err_integral`` -- the volume integrals
of both; ``volume`` -- the mesh volume):

* ``meanU``, ``p_err_mean`` -- the volume-weighted means of ``|U|`` and the pressure error;
* ``maxU_max`` -- the largest ``maxU`` so far;
* ``maxU_10ms`` -- the ``maxU`` at t = 0.01 (TwoPhaseFlow's results.csv; NaN before).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_TIME = 0.01


def derive(history: pd.DataFrame, case: Path) -> pd.DataFrame:
    sampled = np.isclose(history["Time"], SAMPLE_TIME, rtol=0, atol=1e-9)
    return history.assign(
        meanU=history["magU_integral"] / history["volume"],
        p_err_mean=history["p_err_integral"] / history["volume"],
        maxU_max=history["maxU"].cummax(),
        maxU_10ms=history["maxU"].where(sampled).ffill(),
    )
