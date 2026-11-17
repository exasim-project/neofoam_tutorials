"""The static drop's metrics per written time, from the case's fields (``metrics.dat``).

* ``maxU``, ``meanU`` -- the largest and the volume-weighted mean cell ``|U|`` (the
  spurious currents; the drop is at rest), ``maxU_max`` the largest ``maxU`` so far;
* ``Ca``, ``Ca_max`` -- the capillary numbers ``mu_drop |U|max / sigma`` of both;
* ``dp`` -- the Laplace pressure ``mean p_rgh(r < R/2) - mean p_rgh(r > 3R/2)`` (g = 0:
  p_rgh is p), ``r`` the distance to the cylinder axis of ``setAlphaFieldDict``;
* ``sigma_R`` -- ``sigma / R``, ``R`` the radius of the water volume (``sum alpha V``
  over the extruded thickness); ``dp_err`` -- ``|dp / sigma_R - 1|``.

As NeoFOAM's ``test_stationaryDroplet_surface_tension`` measures them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from foamlib import FoamFile

from neofoam_verification.foam import PolyMesh, read_internal_field
from neofoam_verification.suite.workflow import time_directories

ALPHA = "alpha.water"


def metrics(case: Path) -> pd.DataFrame:
    mesh = PolyMesh.read(case)
    centres, volumes, n = mesh.cell_centres, mesh.cell_volumes, mesh.n_cells
    transport = FoamFile(case / "constant" / "transportProperties")
    drop = transport[transport["phases"][0]]
    sigma, mu = float(transport["sigma"]), float(drop["rho"]) * float(drop["nu"])
    cylinder = FoamFile(case / "system" / "setAlphaFieldDict")
    axis = np.asarray(cylinder["direction"], dtype=float)
    axis /= np.linalg.norm(axis)
    thickness = float(np.ptp(mesh.points @ axis))
    offset = centres - np.asarray(cylinder["origin"], dtype=float)
    r = np.linalg.norm(offset - np.outer(offset @ axis, axis), axis=1)

    rows = []
    for time in time_directories(case):
        alpha = read_internal_field(time / ALPHA, n)
        mag_u = np.linalg.norm(read_internal_field(time / "U", n), axis=1)
        p_rgh = read_internal_field(time / "p_rgh", n)
        radius = float(np.sqrt(alpha @ volumes / (np.pi * thickness)))
        dp = p_rgh[r < 0.5 * radius].mean() - p_rgh[r > 1.5 * radius].mean()
        rows.append(
            {
                "Time": float(time.name),
                "maxU": mag_u.max(),
                "meanU": mag_u @ volumes / volumes.sum(),
                "dp": dp,
                "sigma_R": sigma / radius,
            }
        )
    table = pd.DataFrame(rows)
    table.insert(3, "maxU_max", table["maxU"].cummax())
    table.insert(4, "Ca", mu * table["maxU"] / sigma)
    table.insert(5, "Ca_max", mu * table["maxU_max"] / sigma)
    table["dp_err"] = (table["dp"] / table["sigma_R"] - 1.0).abs()
    return table
