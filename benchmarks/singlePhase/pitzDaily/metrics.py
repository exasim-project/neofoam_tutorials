"""pitzDaily's metrics per SIMPLE iteration, from ``log.solver`` and the written fields.

Per iteration (``Time``), from the log (NeoN's and OpenFOAM's print the same lines):

* ``Ux_res``, ``Uy_res``, ``p_res``, ``k_res``, ``epsilon_res`` -- the initial residuals
  (NeoN also solves the empty direction Uz: not used);
* ``clock_s`` -- the ``ClockTime`` (whole seconds).

Of the whole run (every row):

* ``iterations`` -- the first iteration whose residuals all meet the tutorial's
  ``residualControl`` (:data:`TOLERANCE`), NaN if none does; ``wall_s`` the last
  ``ClockTime``, ``time_per_iteration_s`` = wall_s / iterations run;
* ``nCells``.

At the written iterations (forward filled), from ``U``:

* ``x_r``, ``x_r_h`` -- the reattachment length: the most downstream x where the ``Ux`` of
  the lower wall's cells downstream of the step (x > 0, the wall at y = -h) changes from
  negative to positive, linear between the faces, and the same over the step height h;
* ``Umin_xh<N>`` -- the smallest ``Ux / U_inlet`` (the backflow) on the profile at
  x / h = N (:data:`STATIONS`);
* ``profile_err`` -- the largest, over the stations, RMS of ``(Ux - Ux_OpenFOAM) / U_inlet``
  against OpenFOAM's profile on the same mesh (``reference/openfoam_profiles.csv``, rows of
  the same ``nCells``; NaN without).

A profile at x is linear in x between the two cell columns of the channel downstream of
the step next to it (they are straight: the blocks' x-edges have one grading), then linear
in y through the column's cell centres and the walls' no-slip. The final profiles are
written to ``postProcessing/profiles.csv`` (``x_h, y, Ux``) for the plots.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from foamlib import FoamFile

from neofoam_tutorials.foam import PolyMesh, read_internal_field
from neofoam_tutorials.suite.workflow import time_directories

STEP = 0.0254  # step height h [m]: the lower wall drops from y = 0 to -h at x = 0
LENGTH = 0.206  # the straight channel downstream of the step, 0 < x < LENGTH
STATIONS = (1, 3, 5, 7)  # profile stations x / h
PROFILE_Y = np.linspace(-STEP, STEP, 41)
U_INLET = 10.0
#: the tutorial's residualControl (initial residuals)
TOLERANCE = {"Ux": 1e-3, "Uy": 1e-3, "p": 1e-2, "k": 1e-3, "epsilon": 1e-3}
OPENFOAM_PROFILES = Path(__file__).with_name("reference") / "openfoam_profiles.csv"
SOLVING = re.compile(r"Solving for (\w+), Initial residual = ([^,]+)")
CLOCK = re.compile(r"ClockTime = (\S+) s")


def residuals(log: Path) -> pd.DataFrame:
    """One row per SIMPLE iteration: the initial residuals and the clock time."""
    rows: list[dict[str, float]] = []
    for line in log.read_text().splitlines():
        solving = SOLVING.search(line)
        if solving:
            if solving.group(1) == "Ux":
                rows.append({"Time": len(rows) + 1.0})
            if rows:
                rows[-1][f"{solving.group(1)}_res"] = float(solving.group(2))
        clock = CLOCK.search(line)
        if clock and rows:
            rows[-1]["clock_s"] = float(clock.group(1))
    table = pd.DataFrame(rows)
    return table[["Time", *(f"{f}_res" for f in TOLERANCE), "clock_s"]]


def converged_at(table: pd.DataFrame) -> float:
    met = np.all([table[f"{f}_res"] < tol for f, tol in TOLERANCE.items()], axis=0)
    return float(table["Time"][met].iloc[0]) if met.any() else float("nan")


def lower_wall(case: Path, mesh: PolyMesh) -> tuple[np.ndarray, np.ndarray]:
    """The lower wall's faces at y = -h downstream of the step: their x and owner cells."""
    patches = dict(FoamFile(case / "constant" / "polyMesh" / "boundary")[None])
    start, n = patches["lowerWall"]["startFace"], patches["lowerWall"]["nFaces"]
    faces = np.arange(start, start + n)
    centres = mesh.face_centres[faces]
    keep = (centres[:, 0] > 0) & (centres[:, 0] < LENGTH) & np.isclose(centres[:, 1], -STEP)
    order = np.argsort(centres[keep, 0])
    return centres[keep, 0][order], mesh.owner[faces[keep]][order]


def reattachment(x: np.ndarray, ux: np.ndarray) -> float:
    """The most downstream x where ``ux`` turns from negative to positive."""
    turns = np.flatnonzero((ux[:-1] < 0) & (ux[1:] >= 0))
    if len(turns) == 0:
        return float("nan")
    i = turns[-1]
    return float(x[i] - ux[i] * (x[i + 1] - x[i]) / (ux[i + 1] - ux[i]))


def profile(centres: np.ndarray, ux: np.ndarray, x: float) -> np.ndarray:
    """``Ux`` on :data:`PROFILE_Y` at ``x`` in the channel downstream of the step."""
    channel = np.flatnonzero((centres[:, 0] > 0) & (centres[:, 0] < LENGTH))
    # a column's centres differ in x by round-off (the cells are not exact rectangles):
    # columns are the runs of the sorted x without a gap above 1 um
    by_x = channel[np.argsort(centres[channel, 0])]
    starts = np.flatnonzero(np.diff(centres[by_x, 0]) > 1e-6) + 1
    columns = np.split(by_x, starts)
    xs = np.array([centres[cells, 0].mean() for cells in columns])
    i = int(np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2))
    values = []
    for cells in columns[i : i + 2]:
        cells = cells[np.argsort(centres[cells, 1])]
        y = np.concatenate([[-STEP], centres[cells, 1], [STEP]])
        values.append(np.interp(PROFILE_Y, y, np.concatenate([[0.0], ux[cells], [0.0]])))
    weight = (x - xs[i]) / (xs[i + 1] - xs[i])
    return (1 - weight) * values[0] + weight * values[1]


def profiles(centres: np.ndarray, ux: np.ndarray) -> pd.DataFrame:
    return pd.concat(
        [
            pd.DataFrame({"x_h": n, "y": PROFILE_Y, "Ux": profile(centres, ux, n * STEP)})
            for n in STATIONS
        ],
        ignore_index=True,
    )


def profile_error(table: pd.DataFrame, n_cells: int) -> float:
    if not OPENFOAM_PROFILES.is_file():
        return float("nan")
    stored = pd.read_csv(OPENFOAM_PROFILES)
    stored = stored[stored["nCells"] == n_cells]
    if stored.empty:
        return float("nan")
    errors = []
    for n in STATIONS:
        diff = table[table["x_h"] == n]["Ux"].to_numpy() - stored[stored["x_h"] == n]["Ux"]
        errors.append(np.sqrt(np.mean(diff.to_numpy() ** 2)) / U_INLET)
    return float(max(errors))


def metrics(case: Path) -> pd.DataFrame:
    mesh = PolyMesh.read(case)
    centres, n = mesh.cell_centres, mesh.n_cells
    wall_x, wall_cells = lower_wall(case, mesh)

    table = residuals(case / "log.solver")
    table["iterations"] = converged_at(table)
    table["wall_s"] = table["clock_s"].iloc[-1]
    table["time_per_iteration_s"] = table["wall_s"] / len(table)
    table["nCells"] = float(n)
    final = None
    for time in time_directories(case):
        if float(time.name) == 0 or not (time / "U").is_file():
            continue
        ux = read_internal_field(time / "U", n)[:, 0]
        final = profiles(centres, ux)
        x_r = reattachment(wall_x, ux[wall_cells])
        row = table["Time"] == float(time.name)
        table.loc[row, "x_r"] = x_r
        table.loc[row, "x_r_h"] = x_r / STEP
        for station in STATIONS:
            minimum = final[final["x_h"] == station]["Ux"].min() / U_INLET
            table.loc[row, f"Umin_xh{station}"] = minimum
        table.loc[row, "profile_err"] = profile_error(final, n)
    if final is not None:
        (case / "postProcessing").mkdir(exist_ok=True)
        final.assign(nCells=n).to_csv(case / "postProcessing" / "profiles.csv", index=False)
    columns = ["x_r", "x_r_h", *(f"Umin_xh{s}" for s in STATIONS), "profile_err"]
    table[columns] = table[columns].ffill()
    return table
