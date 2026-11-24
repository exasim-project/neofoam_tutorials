"""The input and output convention of the ``reconstructInterface`` benchmark solver.

TwoPhaseFlow's ``apps/benchmark/reconstructInterface`` sets alpha from an implicit
function at ``nIter`` centres (:mod:`..foam_random`), reconstructs each and accumulates
``reconstructionError``. NeoFOAM has no implicit functions in the solver, so the samples
are an input: NeoFOAM's ``setAlphaField`` preprocess tool with ``samples: N`` writes
sample ``i`` (1 ... N) of ``system/setAlphaFieldDict``'s shape to time directory ``i``;
the solver writes the same ``error.dat`` (:func:`write_error_dat`).

Imports no NeoFOAM, so the benchmark definitions can use it in any environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from ..foam import Array
from ..foam_random import centres
from ..reconstruction_error import COLUMNS, ReconstructionError
from ..shapes import Cylinder, Shape, Sphere

ERROR_DAT = Path("postProcessing/reconstructionError/0/error.dat")
TIMING_DAT = ERROR_DAT.with_name("timing.dat")


def _init_dict(case: Path) -> dict[str, Any]:
    """``system/setAlphaFieldDict``'s entries."""
    entries: Any = FoamFile(case / "system" / "setAlphaFieldDict").as_dict()
    return dict(entries)


def alpha_name(case: Path) -> str:
    return str(_init_dict(case)["field"]).strip('"')


def sample_centres(case: Path, n_samples: int) -> Array:
    """The centres of the first ``n_samples`` of reconstructInterface's samples."""
    return centres(np.asarray(_init_dict(case)["origin"], dtype=float), n_samples)


def sample_shape(case: Path, centre: Array) -> Shape:
    """The implicit function of ``setAlphaFieldDict`` moved to ``centre``."""
    init = _init_dict(case)
    origin = (float(centre[0]), float(centre[1]), float(centre[2]))
    if init["type"] == "cylinder":
        d = [float(v) for v in init["direction"]]
        return Cylinder(origin=origin, radius=float(init["radius"]), direction=(d[0], d[1], d[2]))
    if init["type"] == "sphere":
        return Sphere(origin=origin, radius=float(init["radius"]))
    raise ValueError(f"setAlphaFieldDict type {init['type']!r}: cylinder or sphere")


def write_error_dat(
    case: Path,
    errors: ReconstructionError,
    k1: float,
    time_value: float,
    cell_centres: Array,
    cell_volumes: Array,
) -> None:
    """``reconstructionError``'s ``error.dat``: curvature NaN, ``length`` mean |C_N - C_P|.

    The cell centres and volumes are the solver's (OpenFOAM's), the face addressing is
    read from ``constant/polyMesh``.
    """
    mesh_dir = case / "constant" / "polyMesh"
    owner: Any = FoamFile(mesh_dir / "owner")[None]
    neighbour: Any = FoamFile(mesh_dir / "neighbour")[None]
    neighbour = np.asarray(neighbour, dtype=np.int64)
    owner = np.asarray(owner, dtype=np.int64)[: len(neighbour)]
    delta = cell_centres[neighbour] - cell_centres[owner]
    values = errors.norms | {
        "LCurvInf": np.nan,
        "LCurv1": np.nan,
        "k1": k1,
        "k2": 0.0,
        "length": float(np.mean(np.sqrt(np.einsum("ij,ij->i", delta, delta)))),
        "nCells": float(len(cell_volumes)),
        "avgVol": float(np.mean(cell_volumes)),
    }
    path = case / ERROR_DAT
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\t".join(["# Time", *COLUMNS])
    row = "\t".join([f"{time_value:.17g}", *(f"{values[c]:.17e}" for c in COLUMNS)])
    path.write_text(f"# reconstructionError\n{header}\n{row}\n")


def write_timing_dat(case: Path, time_value: float, wall_s: float) -> None:
    """``timing.dat`` beside ``error.dat``: the solver's wall time (``wall_s``)."""
    path = case / TIMING_DAT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# reconstructInterface\n# Time\twall_s\n{time_value:.17g}\t{wall_s:.17e}\n")
