"""Advection-flux reference: one isoAdvection step of OpenFOAM-v2406's geometricVoF.

On the curvature cases of :mod:`neofoam_verification.reconstruction` (same mesh, same
initial alpha), ``reference/advectionFluxReference`` (an OpenFOAM utility, built with
wmake into ``$FOAM_USER_APPBIN``) runs ``isoAdvection::advect`` once for every velocity
and Courant number of ``system/advectionFluxReferenceDict`` and every scheme, with
fvSolution's isoAdvection controls ``alpha.<scheme>`` (nAlphaBounds 3, clip, as
interIsoFoam) and ``alpha.<scheme>.unbounded`` (no bounding, no clipping), and replays
``isoAdvection::timeIntegratedFlux()`` face by face with ``cutFaceAdvectTrace`` (a copy
of ``cutFaceAdvect`` that records its intermediate values). The utility stops unless
the trace equals the library's ``cutFaceAdvect`` on every face and the replayed face
flux equals the library's unbounded ``dVf_`` on every face, both bitwise.
``python -m neofoam_verification.advection_flux`` regenerates
``reference/<case>/advection/``.

Velocities: U = U(C) in the cells, U(Cf) on the boundary faces, phi = U(Cf) . Sf
(divergence free: U is linear and the faces are planar); dt = Co/(0.5 max_cells
sum_faces |phi|/V) (OpenFOAM's CourantNo). Conventions as isoAdvection: ``normal`` is the
reconstruction's interface area vector, pointing into the fluid (alpha = 1); the
advection uses ``n0 = -normal/|normal|`` (out of the fluid) and ``Un0 = U(x0) . n0``
with ``U(x0)`` from ``interpolationCellPoint`` (``U_points`` are its point values,
``volPointInterpolation``), x0 = ``centre``.

File format of ``reference/<case>/advection/<scheme>_<velocity>_Co<Co>.npz``
(``np.load``; F faces of the mesh in OpenFOAM's order, internal then boundary, N cells,
P points, m surface cells, r traced faces, K the largest face size, S = K + 2; values
on faces of empty patches are nan):

Inputs
    ``dt``, ``courant`` (the target), ``max_courant`` (0.5 max sum|phi|/V dt) scalars;
    ``face_patch`` (F,) int (-1 internal), ``face_empty`` (F,) bool, ``mag_sf`` (F,);
    ``phi`` (F,); ``U`` (N, 3); ``U_boundary`` (F, 3) (nan on internal faces);
    ``U_points`` (P, 3); ``alpha0`` (N,): the initial alpha (``mesh.npz`` ``alpha``).

Interface (``reconstructionSchemes`` after ``advect``'s ``reconstruct()``)
    ``cells`` (m,) int: ``interfaceLabels()`` with ``normal != 0`` (the surface cells);
    ``normal``, ``centre``, ``n0`` (m, 3); ``Un0`` (m,).

Unit level: one row per call of ``cutFaceAdvect::timeIntegratedFaceFlux``, in
``timeIntegratedFlux()``'s order (for each surface cell its downwind internal faces,
owner with phi >= 0 or neighbour with phi < 0; then the boundary faces of the surface
cells with phi >= 0, empty patches excluded)
    ``flux_cell``, ``flux_interface`` (index into ``cells``), ``flux_face`` (r,) int;
    ``flux_boundary`` (r,) bool; the arguments ``flux_x0``, ``flux_n0`` (r, 3),
    ``flux_Un0``, ``flux_dt``, ``flux_phi``, ``flux_mag_sf`` (r,); the result
    ``flux_dVf`` (r,);
    ``flux_branch`` (r,) int: 0 ``|Un0| <= 1e-12`` (``dVf = phi dt alphaf``,
    ``flux_alpha_f`` = |cut sub-face area|/magSf), 1 nShifts 0 or 2 (``dVf = phi/magSf
    area``, ``flux_area`` the ``timeIntegratedArea``), 2 nShifts > 2 (non-planar face,
    triangle decomposition; neither area nor steps recorded), 3 other nShifts (dVf = 0);
    ``flux_alpha_f``, ``flux_area`` (r,) nan where not defined;
    ``flux_n_shifts`` (r,) int (-1 for branch 0): sign changes of the edge differences
    of the arrival times around the face (``sign(0) = +1``);
    ``flux_n_points`` (r,) int; ``flux_p_times`` (r, K): the point arrival times
    ``((p - x0) . n0)/Un0`` (set to 0 below 10 SMALL) in face point order, nan padded
    (all nan for branch 0);
    ``flux_n_steps`` (r,) int and ``step_*`` (r, S), padded with -1 / nan: the
    contributions of ``timeIntegratedArea``, in order, ``area`` being their running sum
    from 0 (``step_contribution``; ``step_t0``, ``step_t1``, ``step_area0`` the submerged
    area at t0, ``step_alpha``, ``step_beta`` the ``quadAreaCoeffs``); ``step_kind``: 0
    the face was passed before the step (lastTime <= 0, magSf dt pos0(Un0)), 1 it is
    reached after the step (firstTime >= dt, magSf dt neg(Un0)), 2 constant area before
    the interface arrives (firstTime > 0), 3 a quadrilateral between vertex times,
    4 the last quadrilateral up to dt (lastTime > dt), 5 constant area after the
    interface has left (lastTime <= dt, magSf (dt - lastTime) pos0(Un0)).

Assembled level
    ``dVf_upwind`` (F,): ``upwind(phi).flux(alpha0) dt``, i.e. phi (w (alpha_P -
    alpha_N) + alpha_N) dt with w = pos0(phi) inside, phi alpha_b dt on the boundary;
    ``dVf`` (F,): ``timeIntegratedFlux()``'s face flux before bounding, ``dVf_upwind``
    with ``flux_dVf`` at ``flux_face`` (``isoadvected`` (F,) bool marks those faces);
    ``dVf_limited`` (F,): ``dVf_`` after ``limitFluxes`` (nAlphaBounds 3);
    ``alpha_phi`` (F,): ``alphaPhi()`` = ``dVf_limited``/dt;
    ``alpha_unbounded`` (N,): ``advect`` without bounding or clipping, alpha0 -
    surfaceIntegrate(dVf); ``alpha`` (N,): ``advect`` with bounding and clipping.

``reference/<case>/advection/run.json``: OpenFOAM version, velocities, dt, counts.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from .benchmarks import CASES
from .reconstruction import NAMES, REFERENCE, Arrays, _foam, bashrc, mesh_case

UTILITY = REFERENCE / "advectionFluxReference"
OUTPUT = "advectionFluxReference"
DICT = "advectionFluxReferenceDict"

FLUX_COLUMNS = (
    "row cell interface face boundary x0 x0 x0 n0 n0 n0 Un0 dt phi mag_sf"
    " branch n_shifts n_points dVf area alpha_f"
).split()
_INT = {"cell", "interface", "face", "branch", "n_shifts", "n_points"}
STEP_COLUMNS = ("kind", "t0", "t1", "area0", "alpha", "beta", "contribution")


def settings(name: str, case: Path | None = None) -> Any:
    """``system/advectionFluxReferenceDict`` of ``cases/<name>`` (or of ``case``)."""
    return FoamFile((case or CASES / name) / "system" / DICT)


def runs(name: str) -> list[tuple[str, str, int, Any]]:
    """(scheme, velocity, Courant index, Courant number) of every run, in output order."""
    d = settings(name)
    return [
        (scheme, velocity, i, co)
        for velocity in d["velocities"]
        for i, co in enumerate(d["courantNumbers"])
        for scheme in d["schemes"]
    ]


def run_key(scheme: str, velocity: str, co: Any) -> str:
    return f"{scheme}_{velocity}_Co{co}"


def run_reference(name: str, dest: Path) -> Path:
    """Mesh the case in ``dest``, build and run advectionFluxReference; returns ``dest``."""
    mesh_case(name, dest)
    _foam(dest, f'wmake "{UTILITY}"')
    _foam(dest, "advectionFluxReference")
    return dest


def _rows(path: Path) -> list[list[str]]:
    return [line.split() for line in path.read_text().splitlines() if not line.startswith("#")]


def _read_run(d: Path, mesh: Arrays) -> Arrays:
    faces = np.loadtxt(d / "faces.dat", ndmin=2)
    cells = np.loadtxt(d / "cells.dat", ndmin=2)
    interface = np.loadtxt(d / "interface.dat", ndmin=2)
    dt, courant, max_courant = np.loadtxt(d / "run.dat")
    flux_data = np.loadtxt(d / "flux.dat", ndmin=2)
    r = len(flux_data)
    assert np.array_equal(flux_data[:, 0], np.arange(r))
    flux: Arrays = {}
    col = 1
    for c in dict.fromkeys(FLUX_COLUMNS[1:]):
        width = FLUX_COLUMNS.count(c)
        values = flux_data[:, col : col + width]
        flux[f"flux_{c}"] = values if width == 3 else values[:, 0]
        col += width
    assert col == flux_data.shape[1]
    for c in _INT:
        flux[f"flux_{c}"] = flux[f"flux_{c}"].astype(np.int64)
    flux["flux_boundary"] = flux["flux_boundary"].astype(bool)

    k = int(flux["flux_n_points"].max())
    p_times = np.full((r, k), np.nan)
    for row in _rows(d / "pTimes.dat"):
        times = [float(v) for v in row[1:]]
        p_times[int(row[0]), : len(times)] = times
    steps: dict[int, list[list[float]]] = {}
    for row in _rows(d / "steps.dat"):
        steps.setdefault(int(row[0]), []).append([float(v) for v in row[1:]])
    s = k + 2
    assert all(len(v) <= s for v in steps.values())
    step = np.full((r, s, len(STEP_COLUMNS)), np.nan)
    n_steps = np.zeros(r, dtype=np.int64)
    for i, row_steps in steps.items():
        step[i, : len(row_steps)] = row_steps
        n_steps[i] = len(row_steps)
    step_kind = np.where(np.isnan(step[:, :, 0]), -1, step[:, :, 0]).astype(np.int64)

    dVf = faces[:, 5]
    isoadvected = np.zeros(len(dVf), dtype=bool)
    isoadvected[flux["flux_face"]] = True
    return {
        "dt": np.array(dt),
        "courant": np.array(courant),
        "max_courant": np.array(max_courant),
        "face_patch": mesh["face_patch"],
        "face_empty": mesh["face_empty"],
        "mag_sf": mesh["mag_sf"],
        "phi": faces[:, 0],
        "U": cells[:, 0:3],
        "U_boundary": faces[:, 1:4],
        "U_points": np.loadtxt(d / "points.dat", ndmin=2),
        "alpha0": cells[:, 3],
        "cells": interface[:, 0].astype(np.int64),
        "normal": interface[:, 1:4],
        "centre": interface[:, 4:7],
        "n0": interface[:, 7:10],
        "Un0": interface[:, 10],
        **flux,
        "flux_p_times": p_times,
        "flux_n_steps": n_steps,
        "step_kind": step_kind,
        **{f"step_{c}": step[:, :, j] for j, c in enumerate(STEP_COLUMNS) if c != "kind"},
        "dVf_upwind": faces[:, 4],
        "dVf": dVf,
        "isoadvected": isoadvected,
        "dVf_limited": faces[:, 6],
        "alpha_phi": faces[:, 7],
        "alpha_unbounded": cells[:, 4],
        "alpha": cells[:, 5],
    }


def read_output(name: str, case: Path) -> dict[str, Arrays]:
    """The arrays of every run of ``case``, keyed by :func:`run_key`."""
    faces = np.loadtxt(case / OUTPUT / "faces.dat", ndmin=2)
    mesh = {
        "face_patch": faces[:, 0].astype(np.int64),
        "face_empty": faces[:, 1].astype(bool),
        "mag_sf": faces[:, 2],
    }
    return {
        run_key(scheme, velocity, co): _read_run(case / OUTPUT / velocity / f"Co{i}" / scheme, mesh)
        for scheme, velocity, i, co in runs(name)
    }


def reference_dir(name: str) -> Path:
    return REFERENCE / name / "advection"


def load_run(name: str, scheme: str, velocity: str, co: Any) -> Arrays:
    """The arrays of ``reference/<name>/advection/<scheme>_<velocity>_Co<co>.npz``."""
    with np.load(reference_dir(name) / f"{run_key(scheme, velocity, co)}.npz") as f:
        return dict(f)


def write_reference(name: str) -> Path:
    ref = reference_dir(name)
    with tempfile.TemporaryDirectory() as tmp:
        case = run_reference(name, Path(tmp) / name)
        arrays = read_output(name, case)
        d = settings(name, case)
        info = {
            "utility": "reference/advectionFluxReference",
            "bashrc": str(bashrc()),
            "openfoam": (case / "log.advectionFluxReference")
            .read_text()
            .split("Build  : ", 1)[1]
            .split("\n", 1)[0]
            .strip(),
            "velocities": {
                v: {k: np.asarray(x).tolist() for k, x in d["velocities"][v].items()}
                for v in d["velocities"]
            },
            "runs": {
                key: {
                    "dt": float(a["dt"]),
                    "surface_cells": len(a["cells"]),
                    "traced_faces": len(a["flux_face"]),
                    "branches": np.bincount(a["flux_branch"], minlength=4).tolist(),
                    "limited_faces": int(np.sum((a["dVf_limited"] != a["dVf"]) & ~a["face_empty"])),
                }
                for key, a in arrays.items()
            },
        }
    ref.mkdir(parents=True, exist_ok=True)
    for key, a in arrays.items():
        np.savez_compressed(ref / f"{key}.npz", **a)
    (ref / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return ref


if __name__ == "__main__":
    for n in NAMES:
        print(f"{n}: {write_reference(n)}")
