"""NeoFOAM's setAlphaField script: the tutorial's setFieldsDict, boxToCell by cell centre.

Water (alpha 1) in the cells whose centre lies in the box ``COLUMN``, air elsewhere: the
column a = 0.1461 wide and 2a high (Martin & Moyce's n^2 = 2). Not NeoFOAM's setFields
tool: it corrects the boundary conditions after writing, and the atmosphere's inletOutlet
cannot without a flux field (``failed lookup of phi``).
"""

from typing import Any

import numpy as np
from neofoam.preprocess import IsoVolumeFractions

#: the tutorial's boxToCell box (setFieldsDict), lower and upper corner
COLUMN = ((0.0, 0.0, -1.0), (0.1461, 0.292, 1.0))


def set_alpha(mesh: Any) -> dict[str, IsoVolumeFractions]:
    centres = np.asarray(mesh.C().internalField())
    inside = np.all((centres >= COLUMN[0]) & (centres <= COLUMN[1]), axis=1)
    return {"alpha.water": IsoVolumeFractions(cells=inside.astype(float), patches={})}
