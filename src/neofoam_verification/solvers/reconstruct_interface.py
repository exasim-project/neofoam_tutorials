"""``reconstructInterface`` on NeoFOAM: the benchmark solver of the reconstruction benchmarks.

TwoPhaseFlow's ``apps/benchmark/reconstructInterface`` sets alpha from the implicit
function of ``system/initAlphaFieldDict`` at ``nIter`` centres (:mod:`..foam_random`),
reconstructs each and accumulates ``reconstructionError``. NeoFOAM has no implicit
functions, so the samples are an input here: :func:`alpha_samples`, a case-preparation
step, writes sample ``i`` (1 ... nIter) with OpenFOAM's ``setAlphaField`` to time
directory ``i``. :func:`run` reconstructs each sample with NeoFOAM's own reconstruction
(no algorithm of it lives here) and writes the same
``postProcessing/reconstructionError/0/error.dat`` with :mod:`..reconstruction_error`
(the curvature columns are NaN, the timing column ``k1`` the mean wall time per sample).

Registered with NeoFOAM as ``neofoam solver reconstructInterface`` (pyproject's
``neofoam.solvers`` entry point).

PENDING the NeoFOAM reconstruction-scheme model family: until it exists the scheme
(``solvers.<alpha>.reconstructionScheme``) is read by isoAdvectorNeoN's control reader,
which accepts only ``gradAlpha``, and the reconstruction is
``NeoNCellCutOps.reconstruct_grad_alpha``. With the family, :func:`_reconstructor`
selects the scheme by name, so a newly registered scheme runs with ``--method NAME``.
Not yet run: written against the API of NeoFOAM vof-neon-geometric e90c2183b.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from ..foam import Array, PolyMesh
from ..foam_random import centres
from ..reconstruction_error import COLUMNS, ReconstructionError, sample_errors
from ..shapes import Cylinder, Shape, Sphere

ERROR_DAT = Path("postProcessing/reconstructionError/0/error.dat")


def _init_dict(case: Path) -> dict[str, Any]:
    """``system/initAlphaFieldDict``'s entries."""
    entries: Any = FoamFile(case / "system" / "initAlphaFieldDict").as_dict()
    return dict(entries)


def _field(case: Path) -> str:
    return str(_init_dict(case)["field"]).strip('"')


def _sample_centres(case: Path) -> Array:
    n_iter: Any = FoamFile(case / "system" / "fvSolution")["reconstruction", "nIter"]
    return centres(np.asarray(_init_dict(case)["origin"], dtype=float), int(n_iter))


def alpha_samples(case: Path) -> list[str]:
    """Write ``system/setAlphaFieldDict.<i>`` per sample; the commands that set ``<i>/<alpha>``."""
    field = _field(case)
    commands = []
    for i, centre in enumerate(_sample_centres(case), start=1):
        sample_dict = case / "system" / f"setAlphaFieldDict.{i}"
        shutil.copy(case / "system" / "initAlphaFieldDict", sample_dict)
        FoamFile(sample_dict)["origin"] = [float(c) for c in centre]
        commands.append(
            f"mkdir -p {i} && cp 0/{field} {i}/ && "
            f"setAlphaField -dict system/{sample_dict.name} -time {i}"
        )
    return commands


def _shape(case: Path, centre: Array) -> Shape:
    init = _init_dict(case)
    origin = (float(centre[0]), float(centre[1]), float(centre[2]))
    if init["type"] == "cylinder":
        d = [float(v) for v in init["direction"]]
        return Cylinder(origin=origin, radius=float(init["radius"]), direction=(d[0], d[1], d[2]))
    if init["type"] == "sphere":
        return Sphere(origin=origin, radius=float(init["radius"]))
    raise ValueError(f"initAlphaFieldDict type {init['type']!r}: cylinder or sphere")


def _reconstructor(runtime: Any, alpha_name: str) -> Callable[[Any], tuple[Array, Array]]:
    """The case's scheme as ``alpha -> (centre, normal)`` per cell (host arrays)."""
    from neofoam.algorithms.geometric_vof import NeoNCellCutOps
    from neofoam.solver.incompressibleVoFNeoN.models.alpha_advection.iso_advector import (
        read_iso_advector_controls,
    )

    controls = read_iso_advector_controls(alpha_name)  # refuses every scheme but gradAlpha
    ops = NeoNCellCutOps(
        runtime,
        tol=controls.iso_face_tol,
        plane_search=controls.plane_search,
        surf_cell_tol=controls.surf_cell_tol,
    )

    def reconstruct(alpha: Any) -> tuple[Array, Array]:
        result = ops.reconstruct_grad_alpha(alpha)
        centre = np.asarray(result.centre.copy_to_host()).copy()
        normal = np.asarray(result.normal.copy_to_host()).copy()
        return centre, normal

    return reconstruct


def write_error_dat(case: Path, errors: ReconstructionError, k1: float, time_value: float) -> None:
    """``reconstructionError``'s ``error.dat`` (curvature NaN; ``length`` mean |C_N - C_P|)."""
    mesh = PolyMesh.read(case)
    c = mesh.cell_centres
    delta = c[mesh.neighbour] - c[mesh.owner[: mesh.n_internal_faces]]
    values = errors.norms | {
        "LCurvInf": np.nan,
        "LCurv1": np.nan,
        "k1": k1,
        "k2": 0.0,
        "length": float(np.mean(np.sqrt(np.einsum("ij,ij->i", delta, delta)))),
        "nCells": float(mesh.n_cells),
        "avgVol": float(np.mean(mesh.cell_volumes)),
    }
    path = case / ERROR_DAT
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\t".join(["# Time", *COLUMNS])
    row = "\t".join([f"{time_value:.17g}", *(f"{values[c]:.17e}" for c in COLUMNS)])
    path.write_text(f"# reconstructionError\n{header}\n{row}\n")


def run(argv: list[str]) -> None:
    """``neofoam solver reconstructInterface [-case DIR]``."""
    import pybFoam as pyf
    from neofoam import neofoam_bindings as nfb
    from neofoam.solver.neon_runtime import ensure_neon_initialized, requested_executor

    case = Path(argv[argv.index("-case") + 1]) if "-case" in argv else Path.cwd()
    os.chdir(case)
    case = Path.cwd()
    alpha_name = _field(case)
    ensure_neon_initialized(["reconstructInterface"])
    arg_list = pyf.argList(["reconstructInterface", "-noFunctionObjects"])
    foam_time = pyf.Time(arg_list)  # arg_list must outlive it
    runtime = nfb.create_adapter_run_time(foam_time, requested_executor())
    reconstruct = _reconstructor(runtime, alpha_name)
    errors = ReconstructionError()
    wall = 0.0
    for i, centre in enumerate(_sample_centres(case), start=1):
        foam_time.setTime(float(i), i)  # sample i is time directory i (alpha_samples)
        alpha = nfb.read_scalar_volume_field(runtime, alpha_name)
        start = time.perf_counter()
        cell_centre, normal = reconstruct(alpha)
        wall += time.perf_counter() - start
        errors.add(*sample_errors(_shape(case, centre), cell_centre, normal))
        print(f"sample {i} centre {centre}", flush=True)
    delta_t: Any = FoamFile(case / "system" / "controlDict")["deltaT"]
    write_error_dat(case, errors, wall / len(errors.normal_means), float(delta_t))
    print("End", flush=True)


if __name__ == "__main__":
    run(sys.argv)
