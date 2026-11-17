"""The backends a benchmark's solver runs on, by name.

A backend sources its OpenFOAM (``bashrc``) for every command of a case -- the
preparation steps (blockMesh, setAlphaField) and the solver -- and maps the
benchmark's solver name to its own command:

* ``twophaseflow`` -- the reference: TwoPhaseFlow master's applications built for
  OpenFOAM-v2506 (``$TWOPHASEFLOW_BASHRC``); the solver name is the application.
* ``neofoam``, ``neofoam-cpu``, ``neofoam-gpu`` -- the method under test on NeoN's
  Serial, CPU (OpenMP) and GPU executor: ``neofoam solver <name>``, a benchmark solver
  of :mod:`neofoam_verification.solvers` registered through the ``neofoam.solvers``
  entry-point group (OpenFOAM-v2406, ``$NEOFOAM_BASHRC``, as NeoFOAM is built against).

A new backend is a :class:`Backend` passed to :func:`register`.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Protocol

#: advectorVoF/reconstructInterface can abort (SIGABRT, double free of static type-name
#: words of TwoPhaseFlow's and v2506's libraries) after printing "End"; the run is complete.
EXIT_ABORT = 128 + 6


class Backend(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def bashrc(self) -> Path: ...

    def unavailable(self, solver: str) -> str | None:
        """Why ``solver`` cannot run on this backend here, or None."""
        ...

    def solver_command(self, solver: str) -> str: ...


def _bashrc(variable: str, default: str) -> Path:
    return Path(
        os.environ.get(variable, str(Path.home() / "OpenFOAM" / default / "etc" / "bashrc"))
    )


def _has_command(bashrc: Path, command: str) -> bool:
    probe = f'source "{bashrc}" >/dev/null 2>&1; command -v {command}'
    return subprocess.run(["bash", "-c", probe], capture_output=True).returncode == 0


@dataclass(frozen=True)
class TwoPhaseFlow:
    name: str = "twophaseflow"

    @property
    def bashrc(self) -> Path:
        return _bashrc("TWOPHASEFLOW_BASHRC", "OpenFOAM-v2506")

    def unavailable(self, solver: str) -> str | None:
        if not self.bashrc.is_file():
            return f"no {self.bashrc} ($TWOPHASEFLOW_BASHRC)"
        if not _has_command(self.bashrc, solver):
            return f"{solver} not found under {self.bashrc}"
        return None

    def solver_command(self, solver: str) -> str:
        return solver


@dataclass(frozen=True)
class NeoFOAM:
    name: str = "neofoam"
    #: the NeoN executor, written to system/controlDict's ``executor`` before the solver
    executor: str = "Serial"

    @property
    def bashrc(self) -> Path:
        return _bashrc("NEOFOAM_BASHRC", "OpenFOAM-v2406")

    def unavailable(self, solver: str) -> str | None:
        try:
            metadata.distribution("neofoam")
        except metadata.PackageNotFoundError:
            return "neofoam is not installed in this environment (pixi run install-neofoam)"
        if solver not in metadata.entry_points(group="neofoam.solvers").names:
            return f"no neofoam.solvers entry point {solver!r}"
        return None

    def solver_command(self, solver: str) -> str:
        set_executor = f"foamDictionary -entry executor -set {self.executor} system/controlDict"
        return f"{set_executor} > log.foamDictionary && neofoam solver {solver}"


BACKENDS: dict[str, Backend] = {}


def register(backend: Backend) -> None:
    BACKENDS[backend.name] = backend


register(TwoPhaseFlow())
register(NeoFOAM())
register(NeoFOAM("neofoam-cpu", "CPU"))
register(NeoFOAM("neofoam-gpu", "GPU"))
#: the NeoFOAM backends, one per executor
NEOFOAM_BACKENDS = ("neofoam", "neofoam-cpu", "neofoam-gpu")


def run(backend: Backend, case: Path, command: str, log: str) -> None:
    """Run ``command`` in ``case`` under the backend's OpenFOAM, output to ``case/<log>``."""
    script = f'source "{backend.bashrc}" >/dev/null 2>&1 && {command}'
    with (case / log).open("w") as out:
        returncode = subprocess.run(
            ["bash", "-c", script], cwd=case, stdout=out, stderr=subprocess.STDOUT
        ).returncode
    if returncode == 0:
        return
    if returncode == EXIT_ABORT and "\nEnd\n" in (case / log).read_text():
        return
    raise RuntimeError(f"{command!r} failed ({returncode}) in {case}, see {case / log}")
