"""OpenFOAM's ``setAlphaFieldDict`` for NeoFOAM's ``setAlphaField`` tool, which runs a script.

NeoFOAM's tool calls ``set_alpha(mesh)`` of the case's ``system/setAlphaField.py``; a case
that keeps OpenFOAM's dict (``type`` cylinder or sphere, ``invert false``) re-exports this
module's :func:`set_alpha`, which cuts the cells at the shape's level set (positive inside)
with NeoFOAM's ``cutCellIso``::

    # system/setAlphaField.py
    from neofoam_tutorials.tools.set_alpha_dict import set_alpha  # noqa: F401
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile

from ..foam import Array
from ..shapes import Cylinder, Sphere

DICT = Path("system") / "setAlphaFieldDict"


def shape(spec: Any) -> Cylinder | Sphere:
    """The implicit function of a ``setAlphaFieldDict`` (its entries as foamlib reads them)."""
    if spec.get("invert", False):
        raise ValueError(f"{DICT}: invert true is not supported")
    origin = _point(spec["origin"])
    if spec["type"] == "sphere":
        return Sphere(origin=origin, radius=float(spec["radius"]))
    if spec["type"] == "cylinder":
        direction = _point(spec["direction"])
        return Cylinder(origin=origin, radius=float(spec["radius"]), direction=direction)
    raise ValueError(f"{DICT}: type {spec['type']!r} is not cylinder or sphere")


def _point(value: Any) -> tuple[float, float, float]:
    x, y, z = (float(c) for c in value)
    return (x, y, z)


def level_set(spec: Any, points: Array) -> Array:
    """The shape's values at ``points``: positive inside, zero on its surface."""
    return shape(spec).value(points)


def set_alpha(mesh: Any) -> dict[str, Any]:
    """NeoFOAM's ``set_alpha``: ``{field: volume fractions}`` of the case's dict."""
    from neofoam.preprocess import iso_volume_fractions

    spec = FoamFile(DICT)
    values = level_set(spec, np.asarray(mesh.points(), dtype=float))
    return {str(spec["field"]): iso_volume_fractions(mesh, values)}
