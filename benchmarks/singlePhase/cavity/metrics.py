"""The cavity's metrics per written time, from the case's ``postProcess`` tables (``metrics.dat``).

* ``u_L2``, ``u_Linf`` -- the RMS and the largest ``|u - u_Ghia|`` along the vertical
  centreline x = 0.5, at Ghia, Ghia & Shin's (1982, Table I, Re = 100) 15 interior y;
* ``v_L2``, ``v_Linf`` -- the same of ``v`` along the horizontal centreline y = 0.5
  (Table II); ``reference/ghia1982.csv``;
* ``h`` -- the cell size ``1 / cells per side``;
* ``steps``, ``wall_s``, ``time_per_step_s`` -- of the whole run, from ``log.solver``
  (the steps' ``Courant Number`` lines, the last ``ClockTime``: whole seconds).

The centreline values are linear in x (y) between the two cell columns (rows) next to
the line, then linear in y (x) through the cell centres and the walls' values (the lid
u = 1, else 0) -- the mesh is a uniform blockMesh. The cells are those of the
``u_vertical`` and ``v_horizontal`` tables (``case/system/postProcess.yaml``: the cell
columns, rows, next to the line, every write time); ``maxU`` and ``dU`` (the largest cell
``|U(t) - U(t_prev)|`` since the previous write, the distance to the steady state) are
tables of their own. The final profiles are written to ``postProcessing/profiles.csv``
(columns ``y, u, x, v``) for the plots.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from neofoam_verification.suite.workflow import read_post_process

GHIA = Path(__file__).with_name("reference") / "ghia1982.csv"
CLOCK = re.compile(r"ClockTime = (\S+) s")


def centreline(
    centres: np.ndarray, values: np.ndarray, across: int
) -> tuple[np.ndarray, np.ndarray]:
    """The positions along the line ``centres[:, across] = 0.5`` and ``values`` on it.

    Per cell row (the cells of one position along the line), linear across between the
    row's cells next to the line; any subset of the cells holding them will do.
    """
    along = 1 - across
    positions = np.round(centres[:, along], 12)
    offsets = np.round(centres[:, across], 12)
    stations = np.unique(positions)
    line = []
    for station in stations:
        row = np.flatnonzero(positions == station)
        row = row[np.argsort(offsets[row])]
        line.append(np.interp(0.5, offsets[row], values[row]))
    return stations, np.array(line)


def centrelines(
    centres: np.ndarray, u: np.ndarray, across: tuple[np.ndarray, np.ndarray] | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``(y, u(0.5, y), x, v(x, 0.5))`` through the cell centres and the walls.

    ``centres``, ``u``: the cells next to the vertical line (or all); ``across``: the
    centres and ``u`` of the cells next to the horizontal one (default: the same).
    """
    centres_h, u_h = across if across is not None else (centres, u)
    ys, u_line = centreline(centres, u[:, 0], across=0)
    xs, v_line = centreline(centres_h, u_h[:, 1], across=1)
    y = np.concatenate([[0.0], ys, [1.0]])
    x = np.concatenate([[0.0], xs, [1.0]])
    return y, np.concatenate([[0.0], u_line, [1.0]]), x, np.concatenate([[0.0], v_line, [0.0]])


def _cells(table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """A ``rows`` table's cell centres and ``U``."""
    return table[["x", "y", "z"]].to_numpy(), table[["U_0", "U_1", "U_2"]].to_numpy()


def run_times(log: Path) -> dict[str, float]:
    text = log.read_text()
    steps = text.count("Courant Number")
    clock = CLOCK.findall(text)
    wall = float(clock[-1]) if clock else float("nan")
    return {"steps": steps, "wall_s": wall, "time_per_step_s": wall / max(steps, 1)}


def metrics(case: Path) -> pd.DataFrame:
    post = case / "postProcessing"
    vertical = read_post_process(post / "u_vertical.csv").groupby("Time")
    horizontal = read_post_process(post / "v_horizontal.csv").groupby("Time")
    ghia = pd.read_csv(GHIA).iloc[1:-1]  # the interior points; the ends are the walls
    times = run_times(case / "log.solver")

    rows = []
    for time, cells in vertical:
        y, u_line, x, v_line = centrelines(*_cells(cells), _cells(horizontal.get_group(time)))
        du = np.interp(ghia["y"], y, u_line) - ghia["u"]
        dv = np.interp(ghia["x"], x, v_line) - ghia["v"]
        rows.append(
            {
                "Time": float(time),
                "u_L2": float(np.sqrt(np.mean(du**2))),
                "u_Linf": float(np.abs(du).max()),
                "v_L2": float(np.sqrt(np.mean(dv**2))),
                "v_Linf": float(np.abs(dv).max()),
                "h": 1.0 / (len(y) - 2),
                **times,
            }
        )
    # the final profiles at the mesh's own points, for the plots
    profiles = pd.DataFrame({"y": y, "u": u_line, "x": x, "v": v_line})
    profiles.to_csv(post / "profiles.csv", index=False)
    return pd.DataFrame(rows)
