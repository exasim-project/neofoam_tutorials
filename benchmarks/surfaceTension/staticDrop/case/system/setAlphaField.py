"""NeoFOAM's setAlphaField script: the cylinder of ``system/setAlphaFieldDict``, cut exactly.

OpenFOAM's setAlphaField reads the dict; NeoFOAM's tool runs ``set_alpha(mesh)``, which
cuts the cells at the cylinder's level set (positive inside) with ``cutCellIso``.
"""

from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile
from neofoam.preprocess import IsoVolumeFractions, iso_volume_fractions

from neofoam_tutorials.shapes import Cylinder


def set_alpha(mesh: Any) -> dict[str, IsoVolumeFractions]:
    spec = FoamFile(Path("system") / "setAlphaFieldDict")
    cylinder = Cylinder(
        origin=tuple(spec["origin"]),
        radius=float(spec["radius"]),
        direction=tuple(spec["direction"]),
    )
    level_set = cylinder.value(np.asarray(mesh.points()))
    return {str(spec["field"]): iso_volume_fractions(mesh, level_set)}
