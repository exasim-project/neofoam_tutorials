"""The input and output convention of the ``reconstructInterface`` benchmark solver.

TwoPhaseFlow's ``apps/benchmark/reconstructInterface`` sets alpha from the implicit
function of ``system/initAlphaFieldDict`` at ``nIter`` centres (:mod:`..foam_random`),
reconstructs each and accumulates ``reconstructionError``. NeoFOAM has no implicit
functions, so the samples are an input: :func:`alpha_samples`, a case-preparation step,
writes sample ``i`` (1 ... nIter) with OpenFOAM's ``setAlphaField`` to time directory
``i``; the solver writes the same ``error.dat`` (:func:`write_error_dat`).

Imports no NeoFOAM, so the benchmark definitions can use it in any environment.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from ..foam import Array
from ..foam_random import centres
from ..reconstruction_error import COLUMNS, ReconstructionError
from ..shapes import Cylinder, Shape, Sphere

ERROR_DAT = Path("postProcessing/reconstructionError/0/error.dat")


def _init_dict(case: Path) -> dict[str, Any]:
    """``system/initAlphaFieldDict``'s entries."""
    entries: Any = FoamFile(case / "system" / "initAlphaFieldDict").as_dict()
    return dict(entries)


def alpha_name(case: Path) -> str:
    return str(_init_dict(case)["field"]).strip('"')


def sample_centres(case: Path) -> Array:
    """The centres of reconstructInterface's samples (``reconstruction.nIter`` of fvSolution)."""
    n_iter: Any = FoamFile(case / "system" / "fvSolution")["reconstruction", "nIter"]
    return centres(np.asarray(_init_dict(case)["origin"], dtype=float), int(n_iter))


def alpha_samples(case: Path) -> list[str]:
    """Write ``system/setAlphaFieldDict.<i>`` per sample; the commands that set ``<i>/<alpha>``."""
    field = alpha_name(case)
    commands = []
    for i, centre in enumerate(sample_centres(case), start=1):
        sample_dict = case / "system" / f"setAlphaFieldDict.{i}"
        shutil.copy(case / "system" / "initAlphaFieldDict", sample_dict)
        FoamFile(sample_dict)["origin"] = [float(c) for c in centre]
        commands.append(
            f"mkdir -p {i} && cp 0/{field} {i}/ && "
            f"setAlphaField -dict system/{sample_dict.name} -time {i}"
        )
    return commands


def sample_shape(case: Path, centre: Array) -> Shape:
    """The implicit function of ``initAlphaFieldDict`` moved to ``centre``."""
    init = _init_dict(case)
    origin = (float(centre[0]), float(centre[1]), float(centre[2]))
    if init["type"] == "cylinder":
        d = [float(v) for v in init["direction"]]
        return Cylinder(origin=origin, radius=float(init["radius"]), direction=(d[0], d[1], d[2]))
    if init["type"] == "sphere":
        return Sphere(origin=origin, radius=float(init["radius"]))
    raise ValueError(f"initAlphaFieldDict type {init['type']!r}: cylinder or sphere")


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
