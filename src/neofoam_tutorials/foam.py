"""Small OpenFOAM readers (via foamlib) and OpenFOAM's mesh geometry in numpy.

The geometry is ``primitiveMeshTools::makeFaceCentresAndAreas`` /
``makeCellCentresAndVols`` and ``primitiveMesh::calcCells`` of OpenFOAM-v2406, so cell
volumes and face data agree with OpenFOAM's to round-off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from foamlib import FoamFile

Array = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

ROOTVSMALL = 1.0e-150


def read_internal_field(path: Path, n_cells: int) -> Array:
    """``internalField`` of an OpenFOAM field file, expanded to ``n_cells`` rows if uniform."""
    values = np.asarray(FoamFile(path)["internalField"], dtype=float)
    if values.ndim == 0 or values.shape[0] != n_cells:
        return np.broadcast_to(values, (n_cells, *values.shape)).copy()
    return values


def _face_centres_and_areas(points: Array, faces: list[IntArray]) -> tuple[Array, Array]:
    centres = np.empty((len(faces), 3))
    areas = np.empty((len(faces), 3))
    for i, f in enumerate(faces):
        centres[i], areas[i] = polygon_centre_and_area(points[f])
    return centres, areas


def polygon_centre_and_area(p: Array) -> tuple[Array, Array]:
    """Centre and area vector of a polygon (rows of ``p``), as OpenFOAM computes them."""
    n = len(p)
    if n == 3:
        return (1.0 / 3.0) * (p[0] + p[1] + p[2]), 0.5 * np.cross(p[1] - p[0], p[2] - p[0])
    f_centre = p[0].copy()
    for pi in range(1, n):
        f_centre += p[pi]
    f_centre /= n
    sum_n = np.zeros(3)
    sum_a = 0.0
    sum_ac = np.zeros(3)
    for pi in range(n):
        this_point = p[pi]
        next_point = p[(pi + 1) % n]
        c = this_point + next_point + f_centre
        nv = np.cross(next_point - this_point, f_centre - this_point)
        a = float(np.sqrt(nv @ nv))
        sum_n += nv
        sum_a += a
        sum_ac += a * c
    if sum_a < ROOTVSMALL:
        return f_centre, np.zeros(3)
    return (1.0 / 3.0) * sum_ac / sum_a, 0.5 * sum_n


@dataclass
class PolyMesh:
    """An OpenFOAM polyMesh: points, faces, owner, neighbour (internal faces first)."""

    points: Array
    faces: list[IntArray]
    owner: IntArray
    neighbour: IntArray
    _geometry: dict[str, Array] = field(default_factory=dict, repr=False)

    @classmethod
    def read(cls, case: Path) -> PolyMesh:
        mesh_dir = case / "constant" / "polyMesh"
        faces: Any = FoamFile(mesh_dir / "faces")[None]
        return cls(
            points=np.asarray(FoamFile(mesh_dir / "points")[None], dtype=float),
            faces=[np.asarray(f, dtype=np.int64) for f in faces],
            owner=np.asarray(FoamFile(mesh_dir / "owner")[None], dtype=np.int64),
            neighbour=np.asarray(FoamFile(mesh_dir / "neighbour")[None], dtype=np.int64),
        )

    @property
    def n_cells(self) -> int:
        return int(self.owner.max()) + 1

    @property
    def n_internal_faces(self) -> int:
        return len(self.neighbour)

    @cached_property
    def cells(self) -> list[list[int]]:
        """Faces of each cell in OpenFOAM's order (owned faces, then neighboured faces)."""
        cells: list[list[int]] = [[] for _ in range(self.n_cells)]
        for facei, celli in enumerate(self.owner):
            cells[celli].append(facei)
        for facei, celli in enumerate(self.neighbour):
            cells[celli].append(facei)
        return cells

    def _face_geometry(self) -> None:
        if "Cf" not in self._geometry:
            self._geometry["Cf"], self._geometry["Sf"] = _face_centres_and_areas(
                self.points, self.faces
            )

    @property
    def face_centres(self) -> Array:
        self._face_geometry()
        return self._geometry["Cf"]

    @property
    def face_areas(self) -> Array:
        self._face_geometry()
        return self._geometry["Sf"]

    def _cell_geometry(self) -> None:
        if "V" in self._geometry:
            return
        fc, fa = self.face_centres, self.face_areas
        own, nei = self.owner, self.neighbour
        n = self.n_cells
        c_est = np.zeros((n, 3))
        n_cell_faces = np.zeros(n)
        np.add.at(c_est, own, fc)
        np.add.at(n_cell_faces, own, 1.0)
        np.add.at(c_est, nei, fc[: len(nei)])
        np.add.at(n_cell_faces, nei, 1.0)
        c_est /= n_cell_faces[:, None]
        centres = np.zeros((n, 3))
        vols = np.zeros(n)
        for facei, celli in enumerate(own):
            pyr3 = fa[facei] @ (fc[facei] - c_est[celli])
            centres[celli] += pyr3 * (0.75 * fc[facei] + 0.25 * c_est[celli])
            vols[celli] += pyr3
        for facei, celli in enumerate(nei):
            pyr3 = fa[facei] @ (c_est[celli] - fc[facei])
            centres[celli] += pyr3 * (0.75 * fc[facei] + 0.25 * c_est[celli])
            vols[celli] += pyr3
        small = np.abs(vols) <= 1.0e-300
        centres[~small] /= vols[~small, None]
        centres[small] = c_est[small]
        self._geometry["C"] = centres
        self._geometry["V"] = vols * (1.0 / 3.0)

    @property
    def cell_centres(self) -> Array:
        self._cell_geometry()
        return self._geometry["C"]

    @property
    def cell_volumes(self) -> Array:
        self._cell_geometry()
        return self._geometry["V"]
