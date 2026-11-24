"""Interface-reconstruction reference: OpenFOAM-v2406's geometricVoF on a known interface.

After TwoPhaseFlow's ``apps/benchmark/reconstructInterface`` on the
``run/benchmark/surfaceTension`` cases (one iteration, fixed origin, no curvature):
``cases/<case>/`` is meshed (blockMesh, or gmshToFoam of the committed ``.msh``) and
``reference/reconstructionReference`` (an OpenFOAM utility, built with wmake into
``$FOAM_USER_APPBIN``) sets alpha1 from the implicit function of
``system/initAlphaFieldDict`` with ``cutCellIso`` (as setAlphaField; TwoPhaseFlow's
benchmark can also use ``cutCellImpFunc``, which v2406 does not have), reconstructs
the interface with each scheme of ``system/reconstructionReferenceDict`` and evaluates
``cutCellPLIC::calcSubCell`` and ``surfaceIteratorPLIC::vofCutCell`` in every cell
with a non-zero interface normal. ``python -m neofoam_tutorials.reconstruction``
regenerates ``reference/<case>/``.

File format (``np.load``; n cells, m interface cells, P = 8 planes, K = 12 cuts):

``reference/<case>/mesh.npz``
    ``points`` (n_points, 3), ``face_points`` (sum of face sizes,) int and
    ``face_offsets`` (n_faces + 1,) int (face i is
    ``face_points[face_offsets[i]:face_offsets[i + 1]]``), ``owner`` (n_faces,) int,
    ``neighbour`` (n_internal_faces,) int: constant/polyMesh;
    ``alpha`` (n,): the initial alpha1 (cutCellIso, clamped to [0, 1]);
    ``cell_centres`` (n, 3), ``cell_volumes`` (n,): OpenFOAM's ``mesh.C()``, ``mesh.V()``.

``reference/<case>/<scheme>.npz`` (scheme ``isoAlpha``, ``plicRDF``, ``gradAlpha``)
    ``cells`` (m,) int: the cells with ``mag(normal) != 0``, ascending;
    ``normal`` (m, 3): ``reconstructionSchemes::normal()``, the interface area vector,
    pointing into the fluid (alpha = 1); ``centre`` (m, 3): ``centre()``;

    ``plane_normal`` (m, P, 3), ``plane_cut_value`` (m, P): the planes handed to
    ``cutCellPLIC::calcSubCell(cell, cut_value, normal)``, i.e. through
    ``C + cut_value normal`` (C the cell centre), the fluid on the side of ``normal``.
    With n0 = normal/|normal|, x0 = centre, f(n) = (p - C) . n over the cell points
    and r = max f(n0) - min f(n0), plane 0 is the reconstructed plane (n0,
    (x0 - C) . n0); 1 and 2 shift it by -r/4 and +r/4; 3 and 4 tilt n0 by 20 degrees
    about a1 = n0 x e / |n0 x e| (e the coordinate axis least aligned with n0, ties
    y, z, x) and a2 = n0 x a1, through x0 (for the 2D cases a2 is the y axis, so plane
    4 stays 2D); 5 and 6 lie outside the cell at max f + r/10 (status 1) and
    min f - r/10 (status -1); 7 is normal (1, 2, 3)/sqrt(14) through C.
    Results: ``plane_status`` (m, P) int (-1 below the plane, i.e. full, 0 cut, 1
    empty), ``plane_alpha`` (``VolumeOfFluid``), ``plane_sub_volume``
    (``subCellVolume``) (m, P); ``plane_face_centre``, ``plane_face_area`` (the cut
    face; its area vector points into the fluid, like ``normal``), ``plane_sub_centre``
    (``subCellCentre``) (m, P, 3);

    ``sd_*``: ``surfaceIteratorPLIC::vofCutCell(cell, alpha_target, 1e-8, 100,
    normal)``, the signed distance (cut value) of the plane with ``normal`` that
    cuts ``alpha_target`` off the cell, for the normals n0 and planes 3 and 4's
    (index k // 4) and the targets (cell alpha, 0.1, 0.5, 0.9) (index k % 4):
    ``sd_normal`` (m, K, 3), ``sd_alpha_target``, ``sd_status`` (the return
    value), ``sd_cut_value``, ``sd_alpha``, ``sd_sub_volume`` (m, K),
    ``sd_face_centre``, ``sd_face_area``, ``sd_sub_centre`` (m, K, 3);

    ``LNormalInf``, ``LNormal1``, ``LCentreInf``, ``LCentre1`` (scalars): TwoPhaseFlow's
    ``reconstructionError`` over the m cells, max and mean of 1 - n0 . grad f/|grad f|
    and of the implicit function's distance |f| at x0.

``reference/<case>/gradAlpha.npz`` also has the normal estimate that gradAlpha hands to
``vofCutCell``, for its k interface cells (``interfaceLabels``, alpha in
(surfCellTol, 1 - surfCellTol), a superset of ``cells``):
    ``grad_cells`` (k,) int; ``grad`` (k, 3): ``gradAlpha::gradSurf``'s
    ``leastSquareGrad<scalar>("polyDegree1", geometricD).grad(C_j - C_i, alpha_j)``, an
    unweighted least-squares fit of alpha_j = a + g . (C_j - C_i) over the stencil
    (normal equations, LU solve; the empty direction of the 2D cases is left out and
    its component is 0); ``stencil_cells`` (sum of stencil sizes,) int and
    ``stencil_offsets`` (k + 1,) int: the ``zoneDistribute`` (``zoneCPCStencil``,
    cell-point-cell) stencil of ``grad_cells[i]`` is
    ``stencil_cells[stencil_offsets[i]:stencil_offsets[i + 1]]``, in OpenFOAM's order (the
    order of the sums of the fit), starting with the cell itself. A label j >= n is the
    boundary face ``n_internal_faces + j - n`` (non-empty, non-coupled patches), entering
    the fit with its face centre and alpha's boundary value (zeroGradient: the owner's
    alpha); the cells are those sharing a point with the cell. The utility checks that
    ``vofCutCell`` with ``grad`` gives the stored ``normal`` and ``centre`` bitwise.

``reference/<case>/run.json``: OpenFOAM version, settings, interface cell counts.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from .benchmarks import CASES
from .foam import IntArray, PolyMesh
from .shapes import Cylinder, Shape, Sphere

REFERENCE = Path(__file__).resolve().parents[2] / "reference"
UTILITY = REFERENCE / "reconstructionReference"
OUTPUT = "reconstructionReference"
NAMES = ("curvature2D", "curvature2DTri", "curvature3D", "curvature3DTri")
SCHEMES = ("isoAlpha", "plicRDF", "gradAlpha")
N_PLANES = 8
N_SIGNED_DISTANCE = 12

# columns of the utility's text tables (after the cell label and the plane/normal index)
_CUT = ("status", "alpha", "sub_volume", "face_centre", "face_area", "sub_centre")
PLANE_COLUMNS = ("normal", "cut_value", *_CUT)
SD_COLUMNS = ("normal", "alpha_target", "status", "cut_value", *_CUT[1:])
_VECTORS = {"normal", "face_centre", "face_area", "sub_centre"}
ERRORS = ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1")
# named arrays of mixed dtype (float, int64), as stored in an .npz file
Arrays = dict[str, Any]


def bashrc() -> Path:
    return Path(
        os.environ.get(
            "OPENFOAM_BASHRC", Path.home() / "OpenFOAM" / "OpenFOAM-v2406" / "etc" / "bashrc"
        )
    )


def have_openfoam() -> bool:
    """Whether ``$OPENFOAM_BASHRC`` (default OpenFOAM-v2406) provides wmake and blockMesh."""
    if not bashrc().is_file():
        return False
    probe = subprocess.run(
        ["bash", "-c", f'source "{bashrc()}" >/dev/null 2>&1; command -v wmake blockMesh'],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0 and len(probe.stdout.split()) == 2


def _foam(case: Path, command: str) -> None:
    log = case / f"log.{command.split()[0]}"
    # WM_NCOMPPROCS: wmake builds with at most two jobs
    script = (
        f'source "{bashrc()}" >/dev/null 2>&1 && export WM_NCOMPPROCS=2 && {command} > "{log}" 2>&1'
    )
    if subprocess.run(["bash", "-c", script], cwd=case).returncode != 0:
        raise RuntimeError(f"{command} failed in {case}, see {log}")


def shape(name: str) -> Shape:
    """The implicit function of ``cases/<name>/system/initAlphaFieldDict``."""
    d: Any = FoamFile(CASES / name / "system" / "initAlphaFieldDict")
    origin = tuple(float(v) for v in d["origin"])
    assert len(origin) == 3
    if d["type"] == "cylinder":
        direction = tuple(float(v) for v in d["direction"])
        assert len(direction) == 3
        return Cylinder(origin=origin, radius=float(d["radius"]), direction=direction)
    assert d["type"] == "sphere"
    return Sphere(origin=origin, radius=float(d["radius"]))


def mesh_case(name: str, dest: Path) -> Path:
    """Copy ``cases/<name>`` to ``dest`` and mesh it (``0.orig`` -> ``0``)."""
    shutil.copytree(CASES / name, dest)
    shutil.copytree(dest / "0.orig", dest / "0")
    if (dest / "system" / "blockMeshDict").is_file():
        _foam(dest, "blockMesh")
    else:
        (msh,) = dest.glob("*.msh")
        _foam(dest, f"gmshToFoam {msh.name}")
        if (dest / "system" / "changeDictionaryDict").is_file():
            _foam(dest, "changeDictionary")
    return dest


def run_reference(name: str, dest: Path) -> Path:
    """Mesh the case in ``dest``, build and run reconstructionReference; returns ``dest``."""
    mesh_case(name, dest)
    _foam(dest, f'wmake "{UTILITY}"')
    _foam(dest, "reconstructionReference")
    return dest


def _table(path: Path, columns: tuple[str, ...], n_per_cell: int) -> Arrays:
    """A utility table (cell, index, columns...) as arrays of shape (m, n_per_cell, ...)."""
    data = np.loadtxt(path, ndmin=2)
    m = len(data) // n_per_cell
    assert m * n_per_cell == len(data)
    data = data.reshape(m, n_per_cell, -1)
    assert np.all(data[:, :, 1] == np.arange(n_per_cell))
    out = {}
    col = 2
    for c in columns:
        width = 3 if c in _VECTORS else 1
        values = data[:, :, col : col + width]
        out[c] = values if width == 3 else values[:, :, 0]
        col += width
    assert col == data.shape[2]
    out["status"] = out["status"].astype(np.int64)
    out["cells"] = data[:, 0, 0].astype(np.int64)
    return out


def _gradient(path: Path) -> Arrays:
    """gradAlpha's gradient table (cell, g, stencil size, stencil...) as arrays."""
    rows = [line.split() for line in path.read_text().splitlines() if not line.startswith("#")]
    sizes = np.array([int(r[4]) for r in rows], dtype=np.int64)
    assert all(len(r) == 5 + n for r, n in zip(rows, sizes))
    return {
        "grad_cells": np.array([int(r[0]) for r in rows], dtype=np.int64),
        "grad": np.array([[float(v) for v in r[1:4]] for r in rows]).reshape(-1, 3),
        "stencil_cells": np.array([int(v) for r in rows for v in r[5:]], dtype=np.int64),
        "stencil_offsets": np.concatenate([[0], np.cumsum(sizes)]).astype(np.int64),
    }


def read_output(case: Path) -> tuple[Arrays, dict[str, Arrays]]:
    """(mesh arrays, per-scheme arrays) of a run, in the layout of the ``.npz`` files."""
    mesh = PolyMesh.read(case)
    cells = np.loadtxt(case / OUTPUT / "cells.dat")
    sizes = np.array([len(f) for f in mesh.faces], dtype=np.int64)
    mesh_arrays = {
        "points": mesh.points,
        "face_points": np.concatenate(mesh.faces).astype(np.int64),
        "face_offsets": np.concatenate([[0], np.cumsum(sizes)]).astype(np.int64),
        "owner": mesh.owner,
        "neighbour": mesh.neighbour,
        "alpha": cells[:, 0],
        "cell_centres": cells[:, 1:4],
        "cell_volumes": cells[:, 4],
    }
    schemes = {}
    for scheme in SCHEMES:
        d = case / OUTPUT / scheme
        interface = np.loadtxt(d / "interface.dat", ndmin=2)
        planes = _table(d / "planes.dat", PLANE_COLUMNS, N_PLANES)
        sd = _table(d / "signedDistance.dat", SD_COLUMNS, N_SIGNED_DISTANCE)
        cell_labels = interface[:, 0].astype(np.int64)
        assert np.array_equal(planes.pop("cells"), cell_labels)
        assert np.array_equal(sd.pop("cells"), cell_labels)
        errors = np.loadtxt(d / "error.dat")
        assert int(errors[4]) == len(cell_labels)
        schemes[scheme] = {
            "cells": cell_labels,
            "normal": interface[:, 1:4],
            "centre": interface[:, 4:7],
            **{f"plane_{k}": v for k, v in planes.items()},
            **{f"sd_{k}": v for k, v in sd.items()},
            **{k: np.array(v) for k, v in zip(ERRORS, errors[:4])},
        }
        if (d / "gradient.dat").is_file():
            schemes[scheme].update(_gradient(d / "gradient.dat"))
    return mesh_arrays, schemes


def reference_dir(name: str) -> Path:
    return REFERENCE / name


def load_mesh(name: str) -> tuple[PolyMesh, Arrays]:
    """The stored mesh as a :class:`PolyMesh`, and the arrays of ``mesh.npz``."""
    with np.load(reference_dir(name) / "mesh.npz") as f:
        arrays = dict(f)
    offsets: IntArray = arrays["face_offsets"]
    faces = [arrays["face_points"][a:b] for a, b in zip(offsets[:-1], offsets[1:])]
    mesh = PolyMesh(
        points=arrays["points"],
        faces=faces,
        owner=arrays["owner"],
        neighbour=arrays["neighbour"],
    )
    return mesh, arrays


def load_scheme(name: str, scheme: str) -> Arrays:
    """The arrays of ``reference/<name>/<scheme>.npz``."""
    with np.load(reference_dir(name) / f"{scheme}.npz") as f:
        return dict(f)


def write_reference(name: str) -> Path:
    ref = reference_dir(name)
    with tempfile.TemporaryDirectory() as tmp:
        case = run_reference(name, Path(tmp) / name)
        mesh_arrays, schemes = read_output(case)
        settings: Any = FoamFile(case / "system" / "reconstructionReferenceDict")
        info = {
            "utility": "reference/reconstructionReference",
            "bashrc": str(bashrc()),
            "openfoam": (case / "log.reconstructionReference")
            .read_text()
            .split("Build  : ", 1)[1]
            .split("\n", 1)[0]
            .strip(),
            "n_cells": len(mesh_arrays["alpha"]),
            "settings": {s: dict(settings[s]) for s in SCHEMES},
            "interface_cells": {s: len(a["cells"]) for s, a in schemes.items()},
        }
    ref.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(ref / "mesh.npz", **mesh_arrays)
    for scheme, arrays in schemes.items():
        np.savez_compressed(ref / f"{scheme}.npz", **arrays)
    (ref / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return ref


if __name__ == "__main__":
    for n in NAMES:
        print(f"{n}: {write_reference(n)}")
