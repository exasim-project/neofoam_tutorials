"""The static drop's derived columns (``collect.derive``), per write time.

From the case's ``postProcess`` tables (``case/system/postProcess.yaml``: ``maxU`` --
the largest cell ``|U|``, the spurious current; ``magU_integral``, ``volume`` -- the
volume integral of ``|U|`` and the mesh volume; ``p_inside``, ``p_outside`` -- the mean
``p_rgh`` within ``r < R/2`` and beyond ``r > 3R/2`` of the cylinder axis; ``water`` --
``sum alpha V``) and the case's files:

* ``meanU`` -- the volume-weighted mean ``|U|``;
* ``maxU_max`` -- the largest ``maxU`` so far;
* ``Ca``, ``Ca_max`` -- the capillary numbers ``mu_drop |U|max / sigma`` of both;
* ``dp`` -- the Laplace pressure ``p_inside - p_outside`` (g = 0: p_rgh is p);
* ``sigma_R`` -- ``sigma / R``, ``R`` the radius of the water volume (``water`` over the
  extruded thickness); ``dp_err`` -- ``|dp / sigma_R - 1|``.

As NeoFOAM's ``test_stationaryDroplet_surface_tension`` measures them. The tables'
selectors use the nominal R = 2 mm of ``setAlphaFieldDict``; on n20, n40, n80 they
select the same cells as R of the water volume (0.3 ... 1 % smaller).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from foamlib import FoamFile

from neofoam_verification.foam import PolyMesh


def derive(history: pd.DataFrame, case: Path) -> pd.DataFrame:
    transport = FoamFile(case / "constant" / "transportProperties")
    drop = transport[transport["phases"][0]]
    sigma, mu = float(transport["sigma"]), float(drop["rho"]) * float(drop["nu"])
    axis = np.asarray(FoamFile(case / "system" / "setAlphaFieldDict")["direction"], dtype=float)
    axis /= np.linalg.norm(axis)
    thickness = float(np.ptp(PolyMesh.read(case).points @ axis))

    radius = np.sqrt(history["water"] / (np.pi * thickness))
    table = history.assign(
        meanU=history["magU_integral"] / history["volume"],
        maxU_max=history["maxU"].cummax(),
        Ca=mu * history["maxU"] / sigma,
        dp=history["p_inside"] - history["p_outside"],
        sigma_R=sigma / radius,
    )
    table["Ca_max"] = mu * table["maxU_max"] / sigma
    table["dp_err"] = (table["dp"] / table["sigma_R"] - 1.0).abs()
    return table
