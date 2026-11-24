"""The external reference: TwoPhaseFlow's C++ ``advectorVoF`` with its MULES scheme.

Each benchmark case is meshed (blockMesh, setAlphaField, and for a generated velocity
the testsuite's generator application, built with wmake) and advected with
``advectorVoF`` (``advectionScheme MULESScheme``) under ``$TWOPHASEFLOW_BASHRC``
(OpenFOAM-v2506 + TwoPhaseFlow master), which also runs TwoPhaseFlow's
``volumeFractionError`` function object. ``reference/<case>/<resolution>/`` keeps

* ``volumeFractionError.dat``: the function object's output, verbatim,
* ``alpha_final.txt``: cell alpha at the end time (17 significant digits),
* ``run.json``: versions, time steps, wall time.

``python -m neofoam_tutorials.reference`` regenerates them.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from .backend import RunResult
from .benchmarks import BENCHMARKS, Benchmark, GeneratedVelocity
from .foam import Array, PolyMesh, read_function_object_dat, read_internal_field
from .metrics import exact_alpha_at, volume_fraction_error

REFERENCE = Path(__file__).resolve().parents[2] / "reference"
TWOPHASEFLOW = "TwoPhaseFlow master ba10702 (~/OpenFOAM/<user>-v2506 build)"
DAT = Path("postProcessing/volumeFractionError/0/volumeFractionError.dat")
# advectorVoF can abort (SIGABRT, double free) after printing "End": TwoPhaseFlow's libVoF
# and libpostProcess and v2506's own libgeometricVoF each free the same static type-name
# words at exit (valgrind: __cxa_finalize). The run is complete and written by then.
EXIT_ABORT = 128 + 6


def bashrc() -> Path:
    return Path(
        os.environ.get(
            "TWOPHASEFLOW_BASHRC", Path.home() / "OpenFOAM" / "OpenFOAM-v2506" / "etc" / "bashrc"
        )
    )


def have_twophaseflow() -> bool:
    """Whether ``$TWOPHASEFLOW_BASHRC`` provides advectorVoF and setAlphaField."""
    if not bashrc().is_file():
        return False
    probe = subprocess.run(
        [
            "bash",
            "-c",
            f'source "{bashrc()}" >/dev/null 2>&1; command -v advectorVoF setAlphaField',
        ],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0 and len(probe.stdout.split()) == 2


def _foam(case: Path, *commands: str) -> None:
    for command in commands:
        log = case / f"log.{command.split()[0]}"
        script = f'source "{bashrc()}" >/dev/null 2>&1 && {command} > "{log}" 2>&1'
        returncode = subprocess.run(["bash", "-c", script], cwd=case).returncode
        if returncode == 0:
            continue
        if returncode == EXIT_ABORT and "\nEnd\n" in log.read_text():
            continue
        raise RuntimeError(f"{command} failed in {case}, see {log}")


def mesh_case(benchmark: Benchmark, dest: Path, resolution: str | None = None) -> Path:
    """Copy the case to ``dest`` and create its mesh and initial fields (blockMesh,
    ``0.orig`` -> ``0``, setAlphaField; a generated velocity's application writes
    ``0/U`` and ``0/phi``)."""
    benchmark.copy_case(dest, resolution)
    shutil.copytree(dest / "0.orig", dest / "0")
    _foam(dest, "blockMesh", "setAlphaField")
    if isinstance(benchmark.velocity, GeneratedVelocity):
        generator = benchmark.velocity.generator
        # built in the repository's case directory, so wmake's objects persist
        _foam(dest, f'wmake "{benchmark.case_dir / generator}"', generator)
    return dest


def read_run(benchmark: Benchmark, case: Path) -> RunResult:
    """Alpha at every write time of an OpenFOAM-format run in ``case``."""
    mesh = PolyMesh.read(case)
    return RunResult(
        case_dir=case,
        times=benchmark.write_times,
        alpha=[
            read_internal_field(case / f"{t:g}" / "alpha.water", mesh.n_cells)
            for t in benchmark.write_times
        ],
        volumes=mesh.cell_volumes,
    )


def run_twophaseflow(
    benchmark: Benchmark,
    dest: Path,
    resolution: str | None = None,
    controls: dict[str, Any] | None = None,
) -> tuple[RunResult, dict[str, object]]:
    """Mesh and run the benchmark with advectorVoF/MULESScheme in ``dest``; with
    ``controls``, advectorVoF reads them (fvSolution ``solvers/alpha.water``) instead."""
    mesh_case(benchmark, dest, resolution)
    if controls is not None:
        FoamFile(dest / "system" / "fvSolution")["solvers", "alpha.water"] = controls
    start = time.perf_counter()
    _foam(dest, "advectorVoF")
    wall = time.perf_counter() - start
    log = (dest / "log.advectorVoF").read_text()
    delta_ts = [float(v) for v in re.findall(r"^deltaT = (\S+)$", log, re.MULTILINE)]
    info: dict[str, object] = {
        "solver": "advectorVoF, advectionScheme "
        + (controls or {}).get("advectionScheme", "MULESScheme"),
        "twophaseflow": TWOPHASEFLOW,
        "bashrc": str(bashrc()),
        "resolution": resolution or benchmark.default_resolution,
        "time_steps": len(re.findall(r"^Time = ", log, re.MULTILINE)),
        "deltaT_first": delta_ts[1] if len(delta_ts) > 1 else None,
        "deltaT_last": delta_ts[-1] if delta_ts else None,
        "wall_time_s": round(wall, 2),
    }
    return read_run(benchmark, dest), info


def evaluate(benchmark: Benchmark, result: RunResult) -> Array:
    """Rows (time, Eshape, Emass, Ebound) of ``volumeFractionError`` for every write
    time after 0, computed in Python from the run's alpha fields."""
    mesh = PolyMesh.read(result.case_dir)
    # advectorVoF scales U with phi by a scalar, which keeps volumeFractionError's choice:
    # a uniform 0/U moves the shape by U0 t, any other the shape stays (U = 0 would too)
    velocity = read_internal_field(result.case_dir / "0" / "U", mesh.n_cells)
    initial_mass = float(np.sum(result.volumes * result.alpha[0]))
    rows = []
    for t, alpha in zip(result.times[1:], result.alpha[1:]):
        alpha_exact = exact_alpha_at(mesh, benchmark.shape, velocity, t)
        e = volume_fraction_error(alpha, result.volumes, alpha_exact, initial_mass)
        rows.append([t, e.Eshape, e.Emass, e.Ebound])
    return np.array(rows)


def reference_dir(benchmark: Benchmark, resolution: str | None = None) -> Path:
    return REFERENCE / benchmark.name / (resolution or benchmark.default_resolution)


def load_reference(benchmark: Benchmark, resolution: str | None = None) -> tuple[Array, Array]:
    """(volumeFractionError rows, final alpha) stored for the benchmark."""
    ref = reference_dir(benchmark, resolution)
    return read_function_object_dat(ref / DAT.name), np.loadtxt(ref / "alpha_final.txt")


def write_reference(benchmark: Benchmark, resolution: str | None = None) -> Path:
    ref = reference_dir(benchmark, resolution)
    with tempfile.TemporaryDirectory() as tmp:
        case = Path(tmp) / benchmark.name
        result, info = run_twophaseflow(benchmark, case, resolution)
        ref.mkdir(parents=True, exist_ok=True)
        shutil.copy(case / DAT, ref / DAT.name)
        np.savetxt(ref / "alpha_final.txt", result.alpha[-1], fmt="%.17g")
    (ref / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return ref


if __name__ == "__main__":
    for b in BENCHMARKS.values():
        for res in b.resolutions:
            print(f"{b.name} {res}: {write_reference(b, res)}")
