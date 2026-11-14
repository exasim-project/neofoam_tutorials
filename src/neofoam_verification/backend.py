"""The adapter to the solver under test: NeoFOAM's MULES advection library.

:func:`run_case` is the one place that calls the library; the tests and the metrics
only see :class:`RunResult`. Backends are ``"openfoam"`` (pybFoam) and ``"neon"``
with an executor ``"Serial"``, ``"CPU"`` or ``"GPU"``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .benchmarks import Benchmark
from .foam import Array

BACKENDS = ("openfoam", "neon")
EXECUTORS = ("Serial", "CPU", "GPU")

# The library runs in NeoFOAM's own environment (its CUDA/Kokkos build and
# OpenFOAM-v2406), not in this pixi environment: run_case starts that interpreter
# with that OpenFOAM sourced and reads the result back from an .npz file.
NEOFOAM_PYTHON = os.environ.get(
    "NEOFOAM_PYTHON",
    str(Path.home() / "libsAndApps/NeoFOAM/.claude/worktrees/stack+VoF/.venv/bin/python"),
)
NEOFOAM_BASHRC = os.environ.get(
    "NEOFOAM_BASHRC", str(Path.home() / "OpenFOAM/OpenFOAM-v2406/etc/bashrc")
)

_DRIVER = """
import sys
from pathlib import Path
import numpy as np
from neofoam.algorithms.vof import advect
case, backend, executor, out = sys.argv[1:5]
r = advect(Path(case), backend, executor)
np.savez(out, times=r.times, alpha=r.alpha, volumes=r.cell_volumes)
"""


@dataclass
class RunResult:
    """Cell alpha at every write time of a run (time 0 included) and the cell volumes.

    ``case_dir`` holds the mesh (``constant/polyMesh``), from which the metrics compute
    ``alphaExact``.
    """

    case_dir: Path
    times: list[float]
    alpha: list[Array]
    volumes: Array


def run_case(
    benchmark: Benchmark,
    backend: str,
    executor: str,
    case_dir: Path,
) -> RunResult:
    """Run ``benchmark`` with the MULES advection library and return alpha per write time.

    ``case_dir`` is a meshed case with its initial field (``reference.mesh_case``):
    the library advects ``0/alpha.water`` with the case's prescribed velocity,
    MULES controls (system/fvSolution) and time-step control (system/controlDict,
    maxAlphaCo) until ``benchmark.end_time``, and the result holds alpha at
    ``benchmark.write_times``.
    """
    if backend not in BACKENDS or executor not in EXECUTORS:
        raise ValueError(f"unknown backend {backend!r} / executor {executor!r}")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "result.npz"
        driver = Path(tmp) / "driver.py"
        driver.write_text(_DRIVER)
        log = case_dir / f"log.advect.{backend}.{executor}"
        command = (
            f'source "{NEOFOAM_BASHRC}" >/dev/null 2>&1 && '
            f'"{NEOFOAM_PYTHON}" -I "{driver}" "{case_dir}" {backend} {executor} "{out}"'
        )
        with log.open("w") as log_file:
            subprocess.run(
                ["bash", "-c", command],
                cwd=case_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                check=True,
                env={**os.environ, "FOAM_SIGFPE": "false"},
            )
        data = np.load(out)
        return RunResult(
            case_dir=case_dir,
            times=[float(t) for t in data["times"]],
            alpha=list(data["alpha"]),
            volumes=data["volumes"],
        )
