"""The cavity's metrics per written time, from the case's fields (``metrics.dat``).

* ``u_L2``, ``u_Linf`` -- the RMS and the largest ``|u - u_Ghia|`` along the vertical
  centreline x = 0.5, at Ghia, Ghia & Shin's (1982, Table I, Re = 100) 15 interior y;
* ``v_L2``, ``v_Linf`` -- the same of ``v`` along the horizontal centreline y = 0.5
  (Table II); ``reference/ghia1982.csv``;
* ``dU`` -- the largest cell ``|U(t) - U(t_prev)|`` since the previous written time (the
  distance to the steady state; NaN at the first);
* ``h`` -- the cell size ``1 / cells per side``;
* ``steps``, ``wall_s``, ``time_per_step_s`` -- of the whole run, from ``log.solver``
  (the steps' ``Courant Number`` lines, the last ``ClockTime``: whole seconds).

The centreline values are linear in x (y) between the two cell columns (rows) next to
the line, then linear in y (x) through the cell centres and the walls' values (the lid
u = 1, else 0) -- the mesh is a uniform blockMesh. The final profiles are written to
``postProcessing/profiles.csv`` (columns ``y, u, x, v``) for the plots.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from neofoam_verification.foam import PolyMesh, read_internal_field
from neofoam_verification.suite.workflow import time_directories

GHIA = Path(__file__).with_name("reference") / "ghia1982.csv"
CLOCK = re.compile(r"ClockTime = (\S+) s")


def _grid(values: np.ndarray, ix: np.ndarray, iy: np.ndarray, n: int) -> np.ndarray:
    grid = np.empty((n, n))
    grid[iy, ix] = values
    return grid


def centrelines(
    centres: np.ndarray, u: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``(y, u(0.5, y), x, v(x, 0.5))`` through the cell centres and the walls."""
    xs, ix = np.unique(np.round(centres[:, 0], 12), return_inverse=True)
    ys, iy = np.unique(np.round(centres[:, 1], 12), return_inverse=True)
    n = len(xs)
    ux, uy = _grid(u[:, 0], ix, iy, n), _grid(u[:, 1], ix, iy, n)
    u_line = np.array([np.interp(0.5, xs, row) for row in ux])
    v_line = np.array([np.interp(0.5, ys, column) for column in uy.T])
    y = np.concatenate([[0.0], ys, [1.0]])
    x = np.concatenate([[0.0], xs, [1.0]])
    return y, np.concatenate([[0.0], u_line, [1.0]]), x, np.concatenate([[0.0], v_line, [0.0]])


def run_times(log: Path) -> dict[str, float]:
    text = log.read_text()
    steps = text.count("Courant Number")
    clock = CLOCK.findall(text)
    wall = float(clock[-1]) if clock else float("nan")
    return {"steps": steps, "wall_s": wall, "time_per_step_s": wall / max(steps, 1)}


def metrics(case: Path) -> pd.DataFrame:
    mesh = PolyMesh.read(case)
    centres, n = mesh.cell_centres, mesh.n_cells
    ghia = pd.read_csv(GHIA).iloc[1:-1]  # the interior points; the ends are the walls
    times = run_times(case / "log.solver")

    rows, previous = [], None
    for time in time_directories(case):
        if not (time / "U").is_file():
            continue
        u = read_internal_field(time / "U", n)
        y, u_line, x, v_line = centrelines(centres, u)
        du = np.interp(ghia["y"], y, u_line) - ghia["u"]
        dv = np.interp(ghia["x"], x, v_line) - ghia["v"]
        change = np.nan if previous is None else np.abs(u - previous).max()
        rows.append(
            {
                "Time": float(time.name),
                "u_L2": float(np.sqrt(np.mean(du**2))),
                "u_Linf": float(np.abs(du).max()),
                "v_L2": float(np.sqrt(np.mean(dv**2))),
                "v_Linf": float(np.abs(dv).max()),
                "dU": change,
                "h": 1.0 / (len(y) - 2),
                **times,
            }
        )
        previous = u
    # the final profiles at the mesh's own points, for the plots
    profiles = pd.DataFrame({"y": y, "u": u_line, "x": x, "v": v_line})
    (case / "postProcessing").mkdir(exist_ok=True)
    profiles.to_csv(case / "postProcessing" / "profiles.csv", index=False)
    return pd.DataFrame(rows)
