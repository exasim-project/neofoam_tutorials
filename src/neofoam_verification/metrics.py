"""TwoPhaseFlow's ``volumeFractionError`` function object on plain arrays.

Transcribed from src/postProcessing/volumeFractionError/volumeFractionError.C
(TwoPhaseFlow master ba10702). At each write time it reports

* ``Eshape`` = sum_c V_c |alpha_c - alphaExact_c|  (``fvc::domainIntegrate``; an absolute
  volume, not normalised),
* ``Emass``  = |sum_c V_c alpha_c - initMass|, ``initMass`` the integral of alpha when the
  function object is constructed (the initial field),
* ``Ebound`` = |max(-min(alpha), max(alpha - 1))|,
* ``celltoCellDist`` = mean over internal faces of |C_N - C_P| (``average(mag(mesh.delta()))``),
* ``Ncells`` and ``avg(CellVol)``.

``alphaExact`` is the volume fraction of the initial shape moved with the velocity: by
``U0 t`` when |U| is uniform (max|U| - min|U| <= SMALL, ``U0`` = U of cell 0), otherwise
the initial shape itself (the periodic benchmarks return to their start). The function
object also writes ``tRec``/``Tadv`` (CPU time per step of the reconstruction and
advection), which are timings and are not reproduced.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cut_cell import SMALL, exact_alpha
from .foam import Array, PolyMesh
from .shapes import Shape

# Columns of volumeFractionError.dat that are reproduced, in file order after Time.
COLUMNS = ("Eshape", "Emass", "Ebound")
GEOMETRY_COLUMNS = ("celltoCellDist", "Ncells", "avgCellVol")
DAT_COLUMNS = ("Time", "Eshape", "Emass", "Ebound", "tRec", "Tadv", *GEOMETRY_COLUMNS)


@dataclass(frozen=True)
class VolumeFractionError:
    Eshape: float
    Emass: float
    Ebound: float


def shape_error(alpha: Array, volumes: Array, alpha_exact: Array) -> float:
    return float(np.sum(volumes * np.abs(alpha - alpha_exact)))


def mass_error(alpha: Array, volumes: Array, initial_mass: float) -> float:
    return float(abs(np.sum(volumes * alpha) - initial_mass))


def bound_error(alpha: Array) -> float:
    return float(abs(max(-alpha.min(), (alpha - 1.0).max())))


def volume_fraction_error(
    alpha: Array, volumes: Array, alpha_exact: Array, initial_mass: float
) -> VolumeFractionError:
    """The three error measures of ``volumeFractionError::write()``."""
    return VolumeFractionError(
        Eshape=shape_error(alpha, volumes, alpha_exact),
        Emass=mass_error(alpha, volumes, initial_mass),
        Ebound=bound_error(alpha),
    )


def exact_shape_at(shape: Shape, cell_velocities: Array, time: float) -> Shape:
    """The shape ``volumeFractionError`` compares against at ``time``."""
    mag_u = np.sqrt(np.einsum("ij,ij->i", cell_velocities, cell_velocities))
    if mag_u.max() - mag_u.min() <= SMALL:
        return shape.translated(cell_velocities[0] * time)
    return shape


def exact_alpha_at(mesh: PolyMesh, shape: Shape, cell_velocities: Array, time: float) -> Array:
    """``alphaExact`` of ``volumeFractionError`` at ``time``."""
    moved = exact_shape_at(shape, cell_velocities, time)
    return exact_alpha(mesh, moved.value(mesh.points))


def mesh_measures(mesh: PolyMesh) -> dict[str, float]:
    """``celltoCellDist``, ``Ncells``, ``avg(CellVol)`` columns of the .dat file."""
    c = mesh.cell_centres
    delta = c[mesh.neighbour] - c[mesh.owner[: mesh.n_internal_faces]]
    return {
        "celltoCellDist": float(np.mean(np.sqrt(np.einsum("ij,ij->i", delta, delta)))),
        "Ncells": float(mesh.n_cells),
        "avgCellVol": float(np.mean(mesh.cell_volumes)),
    }
