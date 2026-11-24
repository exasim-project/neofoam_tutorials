"""``change``: how far a field moved since the table's previous evaluation.

Replaces the values by the largest component of ``|U - U_previous|`` per cell (``|p -
p_previous|`` for a scalar), ``U_previous`` the values of the previous evaluation of
the same table, so ``max`` is the distance to a steady state over the table's
interval. The first evaluation has no previous values: every cell is masked out and
``max`` writes ``-GREAT`` (read as NaN by the benchmark's collect)::

    - name: dU
      source: {type: internal, field: U}
      pipeline: [{type: change}, {type: max, name: dU}]
      write_control: {write_control_type: stepper}

The values are copied to the host (NeoN has no element-wise difference kernel).
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from neofoam.postprocess import InternalDataSet, Node
from pydantic import PrivateAttr

from ._host import HostCells, host


@Node.register
class Change(Node):  # type: ignore[misc]
    """The largest component of ``|field - field_previous|`` per cell (first in the pipeline)."""

    type: Literal["change"] = "change"

    _previous: Any = PrivateAttr(default=None)
    _cells: Any = PrivateAttr(default=None)

    def compute(self, dataset: InternalDataSet) -> InternalDataSet:
        if self._cells is None:
            geometry = dataset.geometry
            self._cells = HostCells(host(geometry.positions()), host(geometry.volumes()))
        values = host(dataset.field).copy()
        if self._previous is None:
            change, mask = np.zeros(len(values)), np.zeros(len(values), dtype=np.int32)
        else:
            difference = np.abs(values - self._previous)
            change = difference if difference.ndim == 1 else difference.max(axis=1)
            mask = None
        self._previous = values
        update = {"name": "change", "field": change, "mask": mask, "geometry": self._cells}
        return dataset.model_copy(update=update)
