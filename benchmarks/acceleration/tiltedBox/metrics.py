"""The tilted box's metrics per written time, from the case's fields (``metrics.dat``).

* ``maxU``, ``meanU`` -- the largest and the volume-weighted mean cell ``|U|`` (the
  spurious currents; the fluids are at rest), ``maxU_max`` the largest ``maxU`` so far,
  ``maxU_10ms`` the ``maxU`` at t = 0.01 (TwoPhaseFlow's results.csv; NaN before);
* ``p_err_max``, ``p_err_mean`` -- the largest and the volume-weighted mean
  ``|p - p_hydrostatic|`` relative to the hydrostatic pressure range in the box.

``p_hydrostatic`` is the exact solution with the initial interface (the plane of
``setAlphaFieldDict``, normal to g) and ``p_rgh = 0`` on the open top (in the air):
``rho_air g.x`` above the plane, ``rho_air g.x_i + rho_water g.(x - x_i)`` below it, at
the cell centres, with incompressibleVoFNeoN's ``gh = g.x`` (no hRef).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from foamlib import FoamFile

from neofoam_verification.foam import PolyMesh, read_internal_field
from neofoam_verification.suite.workflow import time_directories

SAMPLE_TIME = 0.01


def hydrostatic_pressure(case: Path, centres: np.ndarray) -> np.ndarray:
    transport = FoamFile(case / "constant" / "transportProperties")
    water, air = (float(transport[phase]["rho"]) for phase in transport["phases"])
    g = np.asarray(FoamFile(case / "constant" / "g")["value"], dtype=float)
    plane = FoamFile(case / "system" / "setAlphaFieldDict")
    origin = np.asarray(plane["origin"], dtype=float)
    below = (centres - origin) @ np.asarray(plane["normal"], dtype=float) > 0
    gh, gh_interface = centres @ g, origin @ g
    return np.where(below, air * gh_interface + water * (gh - gh_interface), air * gh)


def metrics(case: Path) -> pd.DataFrame:
    mesh = PolyMesh.read(case)
    centres, volumes, n = mesh.cell_centres, mesh.cell_volumes, mesh.n_cells
    p_exact = hydrostatic_pressure(case, centres)
    scale = float(np.ptp(p_exact))

    rows = []
    for time in time_directories(case):
        mag_u = np.linalg.norm(read_internal_field(time / "U", n), axis=1)
        row = {
            "Time": float(time.name),
            "maxU": mag_u.max(),
            "meanU": mag_u @ volumes / volumes.sum(),
        }
        if (time / "p").is_file():  # the solver writes p from the first step on
            error = np.abs(read_internal_field(time / "p", n) - p_exact) / scale
            row |= {"p_err_max": error.max(), "p_err_mean": error @ volumes / volumes.sum()}
        rows.append(row)
    table = pd.DataFrame(rows)
    table.insert(3, "maxU_max", table["maxU"].cummax())
    sampled = np.isclose(table["Time"], SAMPLE_TIME, rtol=0, atol=1e-9)
    table.insert(4, "maxU_10ms", table["maxU"].where(sampled).ffill())
    return table
