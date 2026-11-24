"""``hydrostaticError``: the pressure's distance to the hydrostatic solution of a flat interface.

Replaces the cell values of ``p`` by ``|p - p_hydrostatic| / range(p_hydrostatic)``, so
``max`` and ``mean`` are the largest and the mean relative error. ``p_hydrostatic`` is
the exact solution with the plane interface (``origin``, ``normal`` pointing into the
heavy phase, as setAlphaField's plane) and ``p = rho_light g.x`` above it (``p_rgh = 0``
in the light phase at the open top, ``gh = g.x`` without hRef):
``rho_light g.x_i + rho_heavy g.(x - x_i)`` below the plane, ``rho_light g.x`` above,
at the cell centres; ``range`` is its largest minus its smallest cell value::

    - name: p_err_max
      source: {type: internal, field: p}
      pipeline:
        - {type: hydrostaticError, rho_heavy: 1000, rho_light: 1, g: [0, 0, -9.81],
           origin: [0, 0, 0.1345], normal: [0, 0, -1]}
        - {type: max, name: p_err_max}

The values are copied to the host (NeoN has no element-wise difference kernel); the
cell centres once per run.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from neofoam.postprocess import InternalDataSet, Node
from pydantic import PrivateAttr

from ._host import HostCells, host

Point = tuple[float, float, float]


@Node.register
class HydrostaticError(Node):  # type: ignore[misc]
    """``|p - p_hydrostatic| / range(p_hydrostatic)`` per cell (put it first in the pipeline)."""

    type: Literal["hydrostaticError"] = "hydrostaticError"
    rho_heavy: float
    rho_light: float
    g: Point
    origin: Point
    normal: Point

    _cells: Any = PrivateAttr(default=None)
    _exact: Any = PrivateAttr(default=None)

    def compute(self, dataset: InternalDataSet) -> InternalDataSet:
        if self._cells is None:
            geometry = dataset.geometry
            self._cells = HostCells(host(geometry.positions()), host(geometry.volumes()))
            self._exact = self.pressure(self._cells.positions())
        scale = float(np.ptp(self._exact))
        error = np.abs(host(dataset.field) - self._exact) / scale
        return dataset.model_copy(
            update={"name": "hydrostaticError", "field": error, "geometry": self._cells}
        )

    def pressure(self, centres: Any) -> Any:
        """``p_hydrostatic`` at ``centres``."""
        g, origin = np.asarray(self.g, dtype=float), np.asarray(self.origin, dtype=float)
        below = (centres - origin) @ np.asarray(self.normal, dtype=float) > 0
        gh, gh_interface = centres @ g, origin @ g
        heavy = self.rho_light * gh_interface + self.rho_heavy * (gh - gh_interface)
        return np.where(below, heavy, self.rho_light * gh)
