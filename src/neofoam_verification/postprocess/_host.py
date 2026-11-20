"""Host (numpy) copies of what the members compute with numpy rather than NeoN kernels."""

from __future__ import annotations

from typing import Any

import numpy as np


def host(values: Any) -> Any:
    """``values`` as a host numpy copy; a NeoN vector is copied off its executor.

    Always a copy: an array viewing NeoN's host vector would keep it alive, and freeing it
    after ``Kokkos::finalize`` (an array kept to the interpreter's exit) aborts the run.
    """
    copy_to_host = getattr(values, "copy_to_host", None)
    values = np.asarray(copy_to_host() if copy_to_host is not None else values)
    return values.astype(float, copy=True)


def internal_values(field: Any) -> Any:
    """A registered volume field's cell values as a host numpy copy (pybFoam or NeoN)."""
    internal = getattr(field, "internalField", None)
    if internal is not None:
        return np.asarray(internal()).astype(float, copy=True)
    return host(field.internal_vector())


class HostCells:
    """Cell centres and volumes as host numpy: the geometry of a host-valued dataset.

    A kernel call takes every array of one dataset on one executor, so a member that
    hands on host values hands on host geometry too.
    """

    def __init__(self, positions: Any, volumes: Any) -> None:
        self._positions = np.asarray(positions, dtype=float)
        self._volumes = np.asarray(volumes, dtype=float)

    def positions(self) -> Any:
        return self._positions

    def volumes(self) -> Any:
        return self._volumes
