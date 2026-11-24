"""The output convention of the ``advectorVoF`` benchmark solver.

TwoPhaseFlow's advectorVoF runs the ``volumeFractionError`` function object of
``system/controlDict`` (``functions.volumeFractionError``: the initial shape, its
``writeInterval``); :class:`VolumeFractionErrorTable` evaluates it on the solver's
alpha (:mod:`..metrics`) and writes the same ``volumeFractionError.dat``. Its ``tRec``
is 0 (NeoFOAM's isoAdvector step includes the reconstruction) and ``Tadv`` the mean
wall time of one alpha advection (TwoPhaseFlow's: CPU time). ``timing.dat`` beside it
holds the solver's wall time (``wall_s``) and its number of time steps.

Imports no NeoFOAM, so the benchmark definitions can use it in any environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from ..foam import Array, PolyMesh
from ..metrics import exact_alpha_at, mesh_measures, volume_fraction_error
from ..shapes import Cylinder, Shape, Sphere

ERROR_DAT = Path("postProcessing/volumeFractionError/0/volumeFractionError.dat")
TIMING_DAT = ERROR_DAT.with_name("timing.dat")
# TwoPhaseFlow's header (avg(CellVol) is metrics' avgCellVol)
HEADER = (
    "Time",
    "Eshape",
    "Emass",
    "Ebound",
    "tRec",
    "Tadv",
    "celltoCellDist",
    "Ncells",
    "avg(CellVol)",
)


def function_object(case: Path) -> dict[str, Any]:
    """``functions.volumeFractionError`` of ``system/controlDict``."""
    entries: Any = FoamFile(case / "system" / "controlDict")["functions", "volumeFractionError"]
    return dict(entries)


def initial_shape(fo: dict[str, Any]) -> Shape:
    """The function object's implicit function (``functionType`` cylinder or sphere)."""
    origin = tuple(float(c) for c in fo["origin"])
    if fo["functionType"] == "cylinder":
        d = tuple(float(c) for c in fo["direction"])
        return Cylinder(origin=origin, radius=float(fo["radius"]), direction=d)  # type: ignore[arg-type]
    if fo["functionType"] == "sphere":
        return Sphere(origin=origin, radius=float(fo["radius"]))  # type: ignore[arg-type]
    raise ValueError(f"volumeFractionError functionType {fo['functionType']!r}: cylinder or sphere")


class VolumeFractionErrorTable:
    """``volumeFractionError`` on ``case``: the initial mass from ``alpha0``, a row per
    ``writeInterval`` (``adjustableRunTime``: the interval index of ``t + dt/2``)."""

    def __init__(self, case: Path, alpha0: Array, velocities: Array, start_time: float) -> None:
        fo = function_object(case)
        self.path = case / ERROR_DAT
        self.mesh = PolyMesh.read(case)
        self.shape = initial_shape(fo)
        self.interval = float(fo["writeInterval"])
        self.start_time = start_time
        self.velocities = velocities
        self.initial_mass = float(np.sum(self.mesh.cell_volumes * alpha0))
        self.measures = mesh_measures(self.mesh)
        self.write_index = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("# volumeFractionError\n# " + "\t".join(HEADER) + "\n")

    def due(self, time: float, delta_t: float) -> bool:
        """Whether ``time`` is the function object's next write time (and records it)."""
        index = int((time - self.start_time + 0.5 * delta_t) / self.interval)
        if index <= self.write_index:
            return False
        self.write_index = index
        return True

    def write(self, time: float, alpha: Array, t_adv: float) -> None:
        """Append the row of ``alpha`` at ``time``."""
        alpha_exact = exact_alpha_at(self.mesh, self.shape, self.velocities, time)
        e = volume_fraction_error(alpha, self.mesh.cell_volumes, alpha_exact, self.initial_mass)
        m = self.measures
        values = (time, e.Eshape, e.Emass, e.Ebound, 0.0, t_adv, *m.values())
        with self.path.open("a") as f:
            f.write("\t".join(f"{v:.17e}" for v in values) + "\n")


def write_timing_dat(case: Path, time_value: float, wall_s: float, steps: int) -> None:
    """``timing.dat`` beside the error table: the solver's wall time and time steps."""
    path = case / TIMING_DAT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# advectorVoF\n# Time\twall_s\tsteps\n{time_value:.17g}\t{wall_s:.17e}\t{steps}\n"
    )
