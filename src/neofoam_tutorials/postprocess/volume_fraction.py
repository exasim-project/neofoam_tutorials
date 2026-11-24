"""TwoPhaseFlow's ``volumeFractionError`` as ``postProcess`` sources (cell values on the host).

* ``shapeError`` -- ``|alpha - alpha_exact|`` per cell, so ``volIntegrate`` is Eshape
  (``sum V |alpha - alpha_exact|``). ``alpha_exact`` is the cut-cell volume fraction
  (TwoPhaseFlow's ``cutCellIso``: :func:`neofoam_tutorials.cut_cell.exact_alpha`) of
  the implicit function (:mod:`neofoam_tutorials.shapes`) moved by ``U0 t`` when ``|U|``
  is uniform (``max |U| - min |U| <= SMALL``, ``U0`` the velocity of cell 0), else of the
  shape itself, as the function object does::

      - name: Eshape
        source: {type: shapeError, function_type: cylinder, origin: [0.25, 0, 0.25],
                 radius: 0.2, direction: [0, 1, 0]}
        pipeline: [{type: volIntegrate, name: Eshape}]

* ``startField`` -- a field's values as written at the start time (the earliest time
  directory), so ``volIntegrate`` of ``alpha.water`` is the function object's initial
  mass, which an in-run table (evaluated after each step) cannot see::

      - name: mass0
        source: {type: startField, field: alpha.water}
        pipeline: [{type: volIntegrate, name: mass0}]

Both read the case relative to the working directory (the solver runs in the case, as
NeoFOAM's setAlphaField tool) and hand on host values on the mesh's ``C()``/``V()``.
"""

# NB: no ``from __future__ import annotations`` -- a source's ``resolve`` takes the live
# Context (as NeoFOAM's sources).

from pathlib import Path
from typing import Any, Literal, Optional

import numpy as np
from neofoam.framework.context import Context
from neofoam.postprocess import InternalDataSet, Source
from pydantic import PrivateAttr

from ..cut_cell import SMALL, exact_alpha
from ..foam import PolyMesh, read_internal_field
from ..shapes import Cylinder, Sphere
from ._host import HostCells, internal_values

Point = tuple[float, float, float]


def _cells(mesh: Any) -> HostCells:
    return HostCells(np.asarray(mesh.C().internalField()), np.asarray(mesh.V()))


@Source.register
class ShapeError(Source):  # type: ignore[misc]
    """``|alpha - alpha_exact|`` per cell; ``volIntegrate`` it for Eshape."""

    type: Literal["shapeError"] = "shapeError"
    field: str = "alpha1"
    velocity: str = "U"
    function_type: Literal["cylinder", "sphere"]
    origin: Point
    radius: float
    direction: Optional[Point] = None

    _poly_mesh: Any = PrivateAttr(default=None)

    def resolve(self, ctx: Context) -> InternalDataSet:
        if self._poly_mesh is None:
            self._poly_mesh = PolyMesh.read(Path("."))
        cells = _cells(ctx.mesh)
        velocities = internal_values(ctx.fields[self.velocity])
        mag_u = np.sqrt(np.einsum("ij,ij->i", velocities, velocities))
        origin = np.asarray(self.origin, dtype=float)
        if mag_u.max() - mag_u.min() <= SMALL:
            origin = origin + velocities[0] * ctx.time.value
        exact = exact_alpha(self._poly_mesh, self._shape(origin).value(self._poly_mesh.points))
        alpha = internal_values(ctx.fields[self.field])
        return InternalDataSet(name="shapeError", field=np.abs(alpha - exact), geometry=cells)

    def _shape(self, origin: Any) -> Cylinder | Sphere:
        centre = (float(origin[0]), float(origin[1]), float(origin[2]))
        if self.function_type == "sphere":
            return Sphere(origin=centre, radius=self.radius)
        assert self.direction is not None, "shapeError: a cylinder needs a direction"
        return Cylinder(origin=centre, radius=self.radius, direction=self.direction)


@Source.register
class StartField(Source):  # type: ignore[misc]
    """A scalar field as written at the start time (read once, on the first evaluation)."""

    type: Literal["startField"] = "startField"
    #: the name on disk (``alpha.water``), not the registry key
    field: str

    _values: Any = PrivateAttr(default=None)

    def resolve(self, ctx: Context) -> InternalDataSet:
        cells = _cells(ctx.mesh)
        if self._values is None:
            start = min((p for p in Path(".").iterdir() if _is_time(p.name)), key=_time)
            self._values = read_internal_field(start / self.field, len(cells.volumes()))
        return InternalDataSet(name=self.field, field=self._values, geometry=cells)


def _is_time(name: str) -> bool:
    try:
        float(name)
    except ValueError:
        return False
    return True


def _time(path: Path) -> float:
    return float(path.name)
