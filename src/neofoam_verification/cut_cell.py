"""Exact volume fraction of an implicit function on a polyhedral mesh.

A transcription of TwoPhaseFlow's ``cutFaceIso``/``cutFace::calcSubFace``,
``cutCellIso::calcSubCell`` and ``cutCell::calcCellData``/``calcGeomDataCutFace``
(src/VoF/cellCuts, TwoPhaseFlow master ba10702), which ``volumeFractionError`` uses
for ``alphaExact``: the function's point values are linearly interpolated along the
edges, each face is cut at the 0-isoline, and the submerged sub-cell is closed by the
iso face; its volume over the cell volume is the volume fraction.
"""

from __future__ import annotations

import numpy as np

from .foam import ROOTVSMALL, Array, PolyMesh, polygon_centre_and_area

SMALL = 1.0e-15
VSMALL = 1.0e-300


def _sub_face(mesh: PolyMesh, facei: int, f: Array) -> tuple[int, Array, Array, list[Array]]:
    """``cutFaceIso::calcSubFace`` at cut value 0: (status, centre, area, surface points).

    Status -1: face below the isosurface (submerged), 1: above, 0: cut.
    """
    face = mesh.faces[facei]
    status = f[face].copy()
    status[np.abs(status) < 10 * SMALL] = 0.0
    submerged = np.nonzero(status > 10 * SMALL)[0]
    if len(submerged) == len(face):
        return -1, mesh.face_centres[facei], mesh.face_areas[facei], []
    if len(submerged) == 0:
        return 1, np.zeros(3), np.zeros(3), []

    points = mesh.points
    first = int(submerged[0])
    n = len(face)
    sub_face_points: list[Array] = []
    surface_points: list[Array] = []
    for i in range(first, first + n):
        idx = i % n
        next_idx = (i + 1) % n
        if status[idx] > 0:
            sub_face_points.append(points[face[idx]])
        elif status[idx] == 0:
            sub_face_points.append(points[face[idx]])
            surface_points.append(points[face[idx]])
        if (status[idx] < 0 and status[next_idx] > 0) or (status[idx] > 0 and status[next_idx] < 0):
            direction = points[face[next_idx]] - points[face[idx]]
            weight = (0.0 - status[idx]) / (status[next_idx] - status[idx])
            p = points[face[idx]] + weight * direction
            sub_face_points.append(p)
            surface_points.append(p)

    if len(sub_face_points) >= 3:
        centre, area = polygon_centre_and_area(np.array(sub_face_points))
        return 0, centre, area, surface_points
    # cutFaceIso keeps its cleared (zero) centre and area here
    return -1, np.zeros(3), np.zeros(3), surface_points


def _iso_face(edges: list[list[Array]], sub_cell_centre: Array) -> tuple[Array, Array]:
    """``cutCell::calcGeomDataCutFace``: area vector and centre of the iso face."""
    f_centre = np.zeros(3)
    n_edge_points = 0
    for edge_points in edges:
        for p in edge_points:
            f_centre += p
            n_edge_points += 1
    if n_edge_points > 0:
        f_centre /= n_edge_points

    sum_n = np.zeros(3)
    sum_a = 0.0
    sum_ac = np.zeros(3)
    for edge_points in edges:
        for pi in range(len(edge_points) - 1):
            next_point = edge_points[pi + 1]
            c = edge_points[pi] + next_point + f_centre
            n = np.cross(next_point - edge_points[pi], f_centre - edge_points[pi])
            a = float(np.sqrt(n @ n))
            sum_n += (1.0 if n @ sum_n >= 0 else -1.0) * n
            sum_a += a
            sum_ac += a * c

    if sum_a < ROOTVSMALL:
        face_centre, face_area = f_centre, np.zeros(3)
    else:
        face_centre, face_area = (1.0 / 3.0) * sum_ac / sum_a, 0.5 * sum_n
    if face_area @ (face_centre - sub_cell_centre) >= 0:
        face_area = -face_area
    return face_area, face_centre


def _sub_cell_volume(centres: list[Array], areas: list[Array]) -> float:
    """``cutCell::calcCellData``: volume of the closed sub-cell."""
    c_est = np.sum(centres, axis=0) / len(centres)
    volume = 0.0
    for c, a in zip(centres, areas):
        volume += max(abs(float(a @ (c - c_est))), VSMALL)
    return volume / 3


def _cell_fraction(mesh: PolyMesh, celli: int, f: Array) -> float:
    """``cutCellIso::calcSubCell(celli, 0)`` followed by ``VolumeOfFluid()``."""
    centres: list[Array] = []
    areas: list[Array] = []
    edges: list[list[Array]] = []
    fully_below = True
    fully_above = True
    n_below = 0
    for facei in mesh.cells[celli]:
        status, centre, area, surface_points = _sub_face(mesh, facei, f)
        if status == 0:
            centres.append(centre)
            areas.append(area)
            edges.append(surface_points)
            fully_below = fully_above = False
        elif status == -1:
            centres.append(centre)
            areas.append(area)
            fully_above = False
            n_below += 1
        else:
            fully_below = False

    if fully_above:
        return 0.0
    if fully_below:
        return 1.0
    face_area, face_centre = _iso_face(edges, np.sum(centres, axis=0) / len(centres))
    if np.sqrt(face_area @ face_area) < 10 * SMALL:
        return 0.0 if n_below == 0 else 1.0
    centres.append(face_centre)
    areas.append(face_area)
    return _sub_cell_volume(centres, areas) / float(mesh.cell_volumes[celli])


def exact_alpha(mesh: PolyMesh, point_values: Array) -> Array:
    """Volume fraction of every cell below the 0-isosurface of ``point_values``.

    Cells whose points are all clearly inside (``f > 10 SMALL``) or all outside are
    classified without cutting, which is what ``calcSubCell`` returns for them.
    """
    alpha = np.zeros(mesh.n_cells)
    for celli, cell_faces in enumerate(mesh.cells):
        cell_points = np.unique(np.concatenate([mesh.faces[fi] for fi in cell_faces]))
        values = point_values[cell_points]
        if np.all(values > 10 * SMALL):
            alpha[celli] = 1.0
        elif np.all(values <= 10 * SMALL):
            alpha[celli] = 0.0
        else:
            alpha[celli] = _cell_fraction(mesh, celli, point_values)
    return alpha
