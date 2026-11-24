"""TwoPhaseFlow's ``reconstructionError`` function object on plain arrays.

Transcribed from src/postProcessing/reconstructionError/reconstructionError.C
(TwoPhaseFlow master ba10702), which ``apps/benchmark/reconstructInterface`` calls once
per interface sample (``nIter`` centres of the implicit function, :mod:`.foam_random`).
For one sample, over the cells with ``mag(normal) != 0``:

* normal error ``1 - n . n_exact``, ``n`` the reconstructed unit normal and ``n_exact``
  the unit ``implicitFunction::grad`` at the reconstructed centre (both point into the
  fluid, alpha = 1);
* centre error ``implicitFunction::distanceToSurfaces`` of the reconstructed centre.

Across the samples ``LNormalInf``/``LCentreInf`` are the largest cell error of any
sample and ``LNormal1``/``LCentre1`` the mean over the samples of each sample's cell
mean (the paper's L_inf and L_1 of arXiv 1801.05382, eqs. 21-22, with the maximum also
taken over the repetitions). The file also holds curvature errors (``LCurvInf``,
``LCurv1``, from ``surfaceForces``), ``k1`` (CPU time per sample), ``k2`` (0),
``length`` (mean |C_N - C_P| over the internal faces), ``nCells`` and ``avgVol``; the
curvature and timing columns are not reproduced here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .foam import Array
from .shapes import Shape

#: The columns of ``postProcessing/reconstructionError/0/error.dat`` after ``Time``.
COLUMNS = (
    "LNormalInf",
    "LNormal1",
    "LCentreInf",
    "LCentre1",
    "LCurvInf",
    "LCurv1",
    "k1",
    "k2",
    "length",
    "nCells",
    "avgVol",
)


def sample_errors(shape: Shape, centre: Array, normal: Array) -> tuple[Array, Array]:
    """Normal and centre error of every interface cell (``mag(normal) != 0``) of one sample.

    ``centre`` and ``normal`` are the reconstruction's cell fields (n, 3); the normal
    need not be unit length.
    """
    magnitude = np.sqrt(np.einsum("ij,ij->i", normal, normal))
    cells = magnitude != 0
    unit = normal[cells] / magnitude[cells, None]
    exact = shape.grad(centre[cells])
    exact = exact / np.sqrt(np.einsum("ij,ij->i", exact, exact))[:, None]
    normal_error = 1.0 - np.einsum("ij,ij->i", unit, exact)
    return normal_error, shape.distance_to_surface(centre[cells])


@dataclass
class ReconstructionError:
    """``reconstructionError::calcError`` accumulated over the samples (``randomMode`` off)."""

    normal_inf: float = 0.0
    centre_inf: float = 0.0
    normal_means: list[float] = field(default_factory=list)
    centre_means: list[float] = field(default_factory=list)

    def add(self, normal_error: Array, centre_error: Array) -> None:
        """One ``calcError`` call: the cell errors of one sample (:func:`sample_errors`)."""
        self.normal_inf = max(self.normal_inf, float(np.max(normal_error)))
        self.centre_inf = max(self.centre_inf, float(np.max(centre_error)))
        self.normal_means.append(float(np.mean(normal_error)))
        self.centre_means.append(float(np.mean(centre_error)))

    @property
    def norms(self) -> dict[str, float]:
        """``LNormalInf``, ``LNormal1``, ``LCentreInf``, ``LCentre1``."""
        return {
            "LNormalInf": self.normal_inf,
            "LNormal1": float(np.mean(self.normal_means)),
            "LCentreInf": self.centre_inf,
            "LCentre1": float(np.mean(self.centre_means)),
        }
