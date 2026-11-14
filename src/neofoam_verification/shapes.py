"""Implicit functions of the initial interfaces, as OpenFOAM's ``implicitFunction``s.

Positive inside the fluid (alpha = 1), zero on the interface: setAlphaField and
TwoPhaseFlow's ``volumeFractionError`` cut every cell at the 0-isosurface of the
function's point values (:mod:`.cut_cell`).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .foam import Array


@dataclass(frozen=True)
class Cylinder:
    """``implicitFunctions::cylinderImplicitFunction``:
    ``(radius - |(I - d d) . (p - origin)|) * scale``, ``d`` the unit axis."""

    origin: tuple[float, float, float]
    radius: float
    direction: tuple[float, float, float]
    scale: float = 1.0

    def value(self, points: Array) -> Array:
        d = np.asarray(self.direction, dtype=float)
        d = d / np.sqrt(d @ d)
        project = np.eye(3) - np.outer(d, d)
        r = (points - np.asarray(self.origin, dtype=float)) @ project.T
        distance = np.sqrt(np.einsum("ij,ij->i", r, r))
        return np.asarray((-distance + self.radius) * self.scale, dtype=float)

    def translated(self, shift: Array) -> Cylinder:
        o = np.asarray(self.origin, dtype=float) + shift
        return replace(self, origin=(float(o[0]), float(o[1]), float(o[2])))


@dataclass(frozen=True)
class Sphere:
    """``implicitFunctions::sphereImplicitFunction``: ``(radius - |p - origin|) * scale``."""

    origin: tuple[float, float, float]
    radius: float
    scale: float = 1.0

    def value(self, points: Array) -> Array:
        r = points - np.asarray(self.origin, dtype=float)
        distance = np.sqrt(np.einsum("ij,ij->i", r, r))
        return np.asarray((-distance + self.radius) * self.scale, dtype=float)

    def translated(self, shift: Array) -> Sphere:
        o = np.asarray(self.origin, dtype=float) + shift
        return replace(self, origin=(float(o[0]), float(o[1]), float(o[2])))


Shape = Cylinder | Sphere
