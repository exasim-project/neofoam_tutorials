"""``phaseExtent``: how far a phase reaches along a direction, e.g. a dam break's surge front.

Replaces the cell values by the cell centre's coordinate along ``direction`` where the
field (a volume fraction) is above ``threshold``, and by the smallest coordinate of the
mesh elsewhere, so ``max`` is the farthest cell centre of the phase; a selector after it
restricts the cells (the bottom row for a surge front)::

    - name: front
      source: {type: internal, field: alpha1}
      pipeline:
        - {type: phaseExtent, direction: [1, 0, 0]}
        - {type: box, min: [0, 0, -1], max: [1, 0.01, 1]}
        - {type: max, name: front}
      write_control: {write_control_type: timeStep, interval: 1}

The values are copied to the host (NeoN has no element-wise comparison kernel); the cell
centres once per run.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from neofoam.postprocess import InternalDataSet, Node
from pydantic import PrivateAttr

from ._host import HostCells, host


@Node.register
class PhaseExtent(Node):  # type: ignore[misc]
    """The coordinate along ``direction`` of the cells inside the phase (first in the pipeline)."""

    type: Literal["phaseExtent"] = "phaseExtent"
    direction: tuple[float, float, float]
    threshold: float = 0.5

    _cells: Any = PrivateAttr(default=None)
    _coordinates: Any = PrivateAttr(default=None)

    def compute(self, dataset: InternalDataSet) -> InternalDataSet:
        if self._cells is None:
            geometry = dataset.geometry
            self._cells = HostCells(host(geometry.positions()), host(geometry.volumes()))
            self._coordinates = self._cells.positions() @ np.asarray(self.direction, dtype=float)
        inside = host(dataset.field) > self.threshold
        extent = np.where(inside, self._coordinates, self._coordinates.min())
        return dataset.model_copy(
            update={"name": "phaseExtent", "field": extent, "geometry": self._cells}
        )
