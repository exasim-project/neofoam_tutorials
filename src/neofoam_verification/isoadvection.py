"""Multi-step isoAdvection reference: OpenFOAM-v2406's geometricVoF in a time loop.

``reference/isoAdvectionReference`` (an OpenFOAM utility, built with wmake into
``$FOAM_USER_APPBIN``) advects alpha with v2406's ``isoAdvection`` as interIsoFoam does
(``advect(zeroField, zeroField)``: limitFluxes with nAlphaBounds 3, then clipping to
[0, 1], snapTol 0; ``Un0`` from ``interpolationCellPoint``) in the time loop of
TwoPhaseFlow's ``advectorVoF`` (dt from ``maxCo``/``maxAlphaCo``, capped by
``maxDeltaT`` and adjusted to hit the write times; the periodic benchmarks scale
phi0 and U0 by ``cos(2 pi (t + dt/2)/period)`` or ``cos(pi (t + dt/2)/spirallingFlow)``
before ``runTime++``). advectorVoF itself passes ``Su = div(phi0) min(alpha, 1)``,
round-off for these solenoidal velocities, which is left out here. The utility checks
its bookkeeping against the library bitwise (see its header).
``python -m neofoam_verification.isoadvection`` regenerates the stored runs.

Runs (:data:`RUNS`): curvature2D (32 x 32 hex, alpha1 by ``cutCellIso``, the velocities
of ``system/isoAdvectionReferenceDict``) and the TwoPhaseFlow benchmarks at their
coarsest resolution (meshed by :func:`.reference.mesh_case`, i.e. v2506's blockMesh,
setAlphaField and the velocity generator, which writes ``0/U`` and ``0/phi``), each for
:data:`SCHEMES` with the isoAdvection controls :data:`CONTROLS`.

File format of ``reference/<case>/isoAdvection/<key>.npz`` (``np.load``; ``<case>``
is ``curvature2D`` or ``<benchmark>/<resolution>``, ``<key>`` is
``<scheme>_<velocity>`` or ``<scheme>``; S steps, N cells, F faces in OpenFOAM's order
(internal then boundary), m surface cells in step 1, k stored alpha fields, w write
times; values on faces of empty patches are nan):

Per step (S,), after step i (1-based, index i - 1)
    ``time``, ``dt``; ``co``, ``alpha_co``: the Courant numbers the step's dt was set
    from (with the previous dt; ``alpha_co`` over cells with 0.01 < alpha < 0.99);
    ``n_iter`` int: limitFluxes iterations (0 ... 3); ``surface_cells`` int (cells with
    a non-zero interface normal); ``mass_unclipped``, ``min_unclipped``,
    ``max_unclipped``: sum V alpha, min, max after limitFluxes (before clipping);
    ``mass``, ``min``, ``max``: after clipping.

Fields
    ``alpha0`` (N,): the initial alpha; ``cell_volumes`` (N,);
    ``snapshot_steps`` (k,) int, ``snapshot_time`` (k,), ``snapshot_alpha`` (k, N):
    alpha after step 1, every ``alpha_interval`` steps and the write times;
    ``write_time``, ``Eshape``, ``Emass``, ``Ebound`` (w,): :mod:`.metrics`'
    volumeFractionError at the write times (the exact shape is the initial one
    translated by U t, rotated by omega t for the rotation, unmoved for the periodic
    benchmarks).

Step 1 (``s1_*``)
    ``s1_U`` (N, 3), ``s1_phi`` (F,): the velocity of step 1 (stored for the 2D cases
    only; the 3D cases' are ``cos(pi dt/(2 spirallingFlow))`` times the meshed case's
    ``0/U``, ``0/phi``); ``s1_dVf_unlimited`` (F,): ``timeIntegratedFlux()``'s face
    volumes (isoAdvected faces plus upwind elsewhere), before limitFluxes;
    ``s1_dVf_limited`` (F,): after limitFluxes; ``s1_alpha_bounds`` (3, N): alpha after
    0, 1, 2 limitFluxes iterations (row 0 is the unbounded update ``alpha0 -
    surfaceIntegrate(dVf_unlimited)``; rows past ``n_iter[0]`` repeat the final value);
    ``s1_alpha_unclipped`` (N,): after limitFluxes; the clipped alpha is
    ``snapshot_alpha[0]``.
    Interface of advect's reconstruct(): ``s1_cells`` (m,) int (``interfaceLabels`` with
    a non-zero normal); ``s1_normal`` (m, 3) (into the fluid), ``s1_x0`` (m, 3) (the
    centre), ``s1_n0`` (m, 3) (``-normal/|normal|``), ``s1_Un0`` (m,): ``U(x0) . n0``,
    ``U(x0)`` by ``interpolationCellPoint``.

``reference/<case>/isoAdvection/run.json``: OpenFOAM version, controls, steps, timings.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from . import reconstruction, reference
from .benchmarks import BENCHMARKS, CASES
from .cut_cell import exact_alpha
from .foam import PolyMesh
from .metrics import exact_shape_at, volume_fraction_error
from .reconstruction import REFERENCE, Arrays, bashrc, shape
from .shapes import Shape

UTILITY = REFERENCE / "isoAdvectionReference"
OUTPUT = "isoAdvectionReference"
DICT = "isoAdvectionReferenceDict"
SCHEMES = ("gradAlpha", "plicRDF")
# isoAdvection's controls (fvSolution solvers alpha.<scheme>); plicRDF without normal
# interpolation, so it has no state between time steps (as the reconstruction reference)
CONTROLS: dict[str, dict[str, Any]] = {
    "gradAlpha": {"reconstructionScheme": "gradAlpha", "isoFaceTol": 1e-8, "surfCellTol": 1e-8},
    "plicRDF": {
        "reconstructionScheme": "plicRDF",
        "isoFaceTol": 1e-8,
        "surfCellTol": 1e-8,
        "tol": 1e-8,
        "iterations": 10,
        "interpolateNormal": False,
    },
}
STEP_COLUMNS = (
    "step time dt co alpha_co n_iter surface_cells"
    " mass_unclipped min_unclipped max_unclipped mass min max"
).split()
_INT = {"step", "n_iter", "surface_cells"}


@dataclass(frozen=True)
class Case:
    name: str  # cases/<name>
    resolution: str | None  # a benchmark resolution, None for curvature2D
    alpha_interval: int  # alpha is stored every alpha_interval steps (0: never)
    store_inputs: bool  # store step 1's U and phi

    @property
    def label(self) -> str:
        return self.name if self.resolution is None else f"{self.name}/{self.resolution}"


CASES_RUN = (
    Case("curvature2D", None, 1, True),
    Case("discUniFlow", "100x60", 0, True),
    Case("vortexShearedDisc", "32x32", 50, True),
    Case("deformationSphere", "32x32x64", 0, False),
    Case("Leveque", "32x32x32", 0, False),
)
RUNS = {c.label: c for c in CASES_RUN}


def velocities(case: Case) -> dict[str, Any]:
    """The curvature velocities (``system/isoAdvectionReferenceDict``), {} otherwise."""
    if case.resolution is not None:
        return {}
    d: Any = FoamFile(CASES / case.name / "system" / DICT)
    return dict(d["velocities"])


def run_keys(case: Case) -> list[tuple[str, str | None]]:
    """(scheme, velocity) of every run of the case, in output order."""
    vel: list[str | None] = list(velocities(case)) or [None]
    return [(s, v) for v in vel for s in SCHEMES]


def run_key(scheme: str, velocity: str | None) -> str:
    return scheme if velocity is None else f"{scheme}_{velocity}"


def _foam(case: Path, command: str, log: str) -> None:
    # WM_NCOMPPROCS=1: wmake builds with one job
    script = (
        f'source "{bashrc()}" >/dev/null 2>&1 && export WM_NCOMPPROCS=1 '
        f'&& {command} > "{case / log}" 2>&1'
    )
    if subprocess.run(["bash", "-c", script], cwd=case).returncode != 0:
        raise RuntimeError(f"{command} failed in {case}, see {case / log}")


def _set_controls(case_dir: Path) -> None:
    solvers = FoamFile(case_dir / "system" / "fvSolution")
    for scheme, controls in CONTROLS.items():
        name = f"alpha.{scheme}"
        solvers["solvers", name] = {**controls, "nAlphaBounds": 3, "clip": False}
        for n in range(3):
            solvers["solvers", f"{name}.b{n}"] = {**controls, "nAlphaBounds": n, "clip": False}
        solvers["solvers", f"{name}.clip"] = {**controls, "nAlphaBounds": 3, "clip": True}


def mesh_case(case: Case, dest: Path) -> Path:
    """Mesh the case in ``dest`` and add the isoAdvection controls to fvSolution."""
    if case.resolution is None:
        reconstruction.mesh_case(case.name, dest)
    else:
        reference.mesh_case(BENCHMARKS[case.name], dest, case.resolution)
    _set_controls(dest)
    return dest


def run_reference(case: Case, dest: Path) -> tuple[Path, dict[str, float]]:
    """Mesh, build and run isoAdvectionReference; (case dir, wall time per run key)."""
    mesh_case(case, dest)
    _foam(dest, f'wmake "{UTILITY}"', "log.wmake")
    wall = {}
    for scheme, velocity in run_keys(case):
        key = run_key(scheme, velocity)
        args = f"-scheme {scheme} -alphaInterval {case.alpha_interval}"
        if velocity is not None:
            spec = velocities(case)[velocity]
            control = FoamFile(dest / "system" / "controlDict")
            for k, v in {
                "endTime": spec["endTime"],
                "writeInterval": spec["writeInterval"],
                "writeControl": "adjustableRunTime",
                "deltaT": 1e-3,
                "adjustTimeStep": True,
                "maxCo": 1e10,
                "maxAlphaCo": FoamFile(dest / "system" / DICT)["maxAlphaCo"],
                "maxDeltaT": 1,
            }.items():
                control[k] = v
            args += f" -velocity {velocity} -alpha alpha1 -implicitFunction"
        start = time.perf_counter()
        _foam(dest, f"isoAdvectionReference {args}", f"log.isoAdvectionReference.{key}")
        wall[key] = round(time.perf_counter() - start, 2)
    return dest, wall


def write_times(case: Case, velocity: str | None) -> list[float]:
    """The write times after 0 (alpha is stored at each)."""
    if case.resolution is not None:
        return BENCHMARKS[case.name].write_times[1:]
    assert velocity is not None
    spec = velocities(case)[velocity]
    n = round(float(spec["endTime"]) / float(spec["writeInterval"]))
    return [i * float(spec["writeInterval"]) for i in range(1, n + 1)]


def exact_shape(case: Case, velocity: str | None, cell_velocities: Any, t: float) -> Shape:
    """The shape volumeFractionError compares against at ``t``."""
    if case.resolution is not None:
        return exact_shape_at(BENCHMARKS[case.name].shape, cell_velocities, t)
    assert velocity is not None
    spec = velocities(case)[velocity]
    s = shape(case.name)
    if spec["type"] == "uniform":
        return s.translated(np.asarray(spec["value"], dtype=float) * t)
    # rotation by omega t about the axis through origin (Rodrigues)
    a = np.asarray(spec["axis"], dtype=float)
    a = a / np.linalg.norm(a)
    o = np.asarray(spec["origin"], dtype=float)
    r = np.asarray(s.origin, dtype=float) - o
    theta = float(spec["omega"]) * t
    rotated = (
        r * math.cos(theta) + np.cross(a, r) * math.sin(theta) + a * (a @ r) * (1 - math.cos(theta))
    )
    return s.translated(rotated - r)


def errors(case: Case, velocity: str | None, mesh: PolyMesh, run: Arrays) -> Arrays:
    """volumeFractionError (:mod:`.metrics`) of the stored alpha at the write times."""
    times = write_times(case, velocity)
    rows = []
    for t in times:
        (i,) = np.flatnonzero(np.isclose(run["snapshot_time"], t, rtol=0, atol=1e-9))
        moved = exact_shape(case, velocity, run["s1_U"], t)
        e = volume_fraction_error(
            run["snapshot_alpha"][i],
            run["cell_volumes"],
            exact_alpha(mesh, moved.value(mesh.points)),
            float(np.sum(run["cell_volumes"] * run["alpha0"])),
        )
        rows.append([e.Eshape, e.Emass, e.Ebound])
    values = np.array(rows).reshape(-1, 3)
    return {
        "write_time": np.array(times),
        **{c: values[:, j] for j, c in enumerate(("Eshape", "Emass", "Ebound"))},
    }


def read_run(case_dir: Path, scheme: str, velocity: str | None) -> Arrays:
    """The arrays of one run in ``case_dir`` (without the errors)."""
    d = case_dir / OUTPUT / (scheme if velocity is None else f"{velocity}/{scheme}")
    data = np.loadtxt(d / "steps.dat", ndmin=2)
    assert data.shape[1] == len(STEP_COLUMNS)
    steps = {c: data[:, j] for j, c in enumerate(STEP_COLUMNS)}
    for c in _INT:
        steps[c] = steps[c].astype(np.int64)
    assert np.array_equal(steps.pop("step"), np.arange(1, len(data) + 1))
    snapshot_steps = sorted(int(p.stem) for p in (d / "alpha").glob("*.dat"))
    assert snapshot_steps[0] == 0
    alpha = np.array([np.loadtxt(d / "alpha" / f"{s}.dat") for s in snapshot_steps])
    snapshot_steps = snapshot_steps[1:]
    faces = np.loadtxt(d / "step1" / "faces.dat", ndmin=2)
    cells = np.loadtxt(d / "step1" / "cells.dat", ndmin=2)
    interface = np.loadtxt(d / "step1" / "interface.dat", ndmin=2)
    assert np.array_equal(cells[:, 3], alpha[0])
    return {
        **steps,
        "alpha0": alpha[0],
        "snapshot_steps": np.array(snapshot_steps, dtype=np.int64),
        "snapshot_time": steps["time"][np.array(snapshot_steps) - 1],
        "snapshot_alpha": alpha[1:],
        "s1_U": cells[:, 0:3],
        "s1_phi": faces[:, 0],
        "s1_dVf_unlimited": faces[:, 1],
        "s1_dVf_limited": faces[:, 2],
        "s1_alpha_bounds": cells[:, 4:7].T.copy(),
        "s1_alpha_unclipped": cells[:, 7],
        "cell_volumes": cells[:, 8],
        "s1_cells": interface[:, 0].astype(np.int64),
        "s1_normal": interface[:, 1:4],
        "s1_x0": interface[:, 4:7],
        "s1_n0": interface[:, 7:10],
        "s1_Un0": interface[:, 10],
    }


def reference_dir(case: Case) -> Path:
    return REFERENCE / case.label / "isoAdvection"


def load_run(label: str, scheme: str, velocity: str | None = None) -> Arrays:
    """The arrays of ``reference/<label>/isoAdvection/<scheme>[_<velocity>].npz``
    (``label`` a key of :data:`RUNS`, e.g. ``curvature2D`` or ``Leveque/32x32x32``)."""
    with np.load(reference_dir(RUNS[label]) / f"{run_key(scheme, velocity)}.npz") as f:
        return dict(f)


def _openfoam_build(log: Path) -> str:
    return log.read_text().split("Build  : ", 1)[1].split("\n", 1)[0].strip()


def write_reference(case: Case) -> Path:
    ref = reference_dir(case)
    with tempfile.TemporaryDirectory() as tmp:
        case_dir, wall = run_reference(case, Path(tmp) / case.name)
        mesh = PolyMesh.read(case_dir)
        arrays = {}
        for scheme, velocity in run_keys(case):
            run = read_run(case_dir, scheme, velocity)
            run.update(errors(case, velocity, mesh, run))
            if not case.store_inputs:
                del run["s1_U"], run["s1_phi"]
            arrays[run_key(scheme, velocity)] = run
        info = {
            "utility": "reference/isoAdvectionReference",
            "bashrc": str(bashrc()),
            "openfoam": _openfoam_build(next(case_dir.glob("log.isoAdvectionReference.*"))),
            "case": case.label,
            "n_cells": mesh.n_cells,
            "controls": CONTROLS,
            "alpha_interval": case.alpha_interval,
            "velocities": {
                v: {k: np.asarray(x).tolist() for k, x in spec.items()}
                for v, spec in velocities(case).items()
            },
            "runs": {
                key: {
                    "steps": len(a["dt"]),
                    "end_time": float(a["time"][-1]),
                    "dt_first": float(a["dt"][0]),
                    "dt_min": float(a["dt"].min()),
                    "dt_max": float(a["dt"].max()),
                    "n_iter": np.bincount(a["n_iter"], minlength=4).tolist(),
                    "surface_cells_step1": len(a["s1_cells"]),
                    "Eshape": a["Eshape"].tolist(),
                    "Ebound": a["Ebound"].tolist(),
                    "Emass": a["Emass"].tolist(),
                    "wall_time_s": wall[key],
                }
                for key, a in arrays.items()
            },
        }
    if ref.exists():
        shutil.rmtree(ref)
    ref.mkdir(parents=True)
    for key, a in arrays.items():
        np.savez_compressed(ref / f"{key}.npz", **a)
    (ref / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return ref


if __name__ == "__main__":
    import sys

    for c in CASES_RUN:
        if len(sys.argv) == 1 or c.name in sys.argv[1:]:
            print(f"{c.label}: {write_reference(c)}")
