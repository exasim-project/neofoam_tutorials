"""The Python cut cell (TwoPhaseFlow's cutCellIso, ``cut_cell.exact_alpha``) and mesh
geometry against the stored OpenFOAM initial alpha of the reconstruction reference."""

from __future__ import annotations

import numpy as np
import pytest

from neofoam_tutorials.cut_cell import exact_alpha
from neofoam_tutorials.reconstruction import NAMES, load_mesh, shape


@pytest.mark.parametrize("name", NAMES)
def test_initial_alpha_is_the_python_cut_cell(name: str) -> None:
    mesh, arrays = load_mesh(name)
    alpha = exact_alpha(mesh, shape(name).value(mesh.points))
    np.testing.assert_allclose(arrays["alpha"], alpha, rtol=0, atol=1e-14)
    np.testing.assert_allclose(arrays["cell_volumes"], mesh.cell_volumes, rtol=1e-12)
    np.testing.assert_allclose(arrays["cell_centres"], mesh.cell_centres, rtol=0, atol=1e-14)
