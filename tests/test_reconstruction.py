"""The stored interface-reconstruction reference (reference/curvature*/).

Without OpenFOAM: the stored files load with the documented shapes, the Python cut cell
(TwoPhaseFlow's cutCellIso, ``cut_cell.exact_alpha``) gives OpenFOAM's initial alpha,
and the stored cuts are consistent with themselves (the reconstructed plane cuts the
cell's alpha, ``vofCutCell`` meets its targets). With OpenFOAM-v2406 (marked
``geometricvof``): a rerun of the utility reproduces the stored arrays bitwise.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neofoam_verification.cut_cell import exact_alpha
from neofoam_verification.reconstruction import (
    N_PLANES,
    N_SIGNED_DISTANCE,
    NAMES,
    SCHEMES,
    have_openfoam,
    load_mesh,
    load_scheme,
    read_output,
    run_reference,
    shape,
)

CASE_SCHEMES = [(n, s) for n in NAMES for s in SCHEMES]
# vofCutCell's tolerance on alpha (reconstructionReferenceDict, plicRDF's isoFaceTol)
TOL = 1e-8


@pytest.mark.parametrize("name", NAMES)
def test_initial_alpha_is_the_python_cut_cell(name: str) -> None:
    mesh, arrays = load_mesh(name)
    alpha = exact_alpha(mesh, shape(name).value(mesh.points))
    np.testing.assert_allclose(arrays["alpha"], alpha, rtol=0, atol=1e-14)
    np.testing.assert_allclose(arrays["cell_volumes"], mesh.cell_volumes, rtol=1e-12)
    np.testing.assert_allclose(arrays["cell_centres"], mesh.cell_centres, rtol=0, atol=1e-14)


@pytest.mark.parametrize("name, scheme", CASE_SCHEMES)
def test_reference_has_the_documented_shapes(name: str, scheme: str) -> None:
    _, mesh = load_mesh(name)
    a = load_scheme(name, scheme)
    m = len(a["cells"])
    assert m > 0
    assert np.all(np.diff(a["cells"]) > 0)
    assert a["cells"][-1] < len(mesh["alpha"])
    for prefix, k in (("plane", N_PLANES), ("sd", N_SIGNED_DISTANCE)):
        for key in ("normal", "face_centre", "face_area", "sub_centre"):
            assert a[f"{prefix}_{key}"].shape == (m, k, 3), key
        for key in ("cut_value", "status", "alpha", "sub_volume"):
            assert a[f"{prefix}_{key}"].shape == (m, k), key
    assert a["sd_alpha_target"].shape == (m, N_SIGNED_DISTANCE)
    assert a["normal"].shape == a["centre"].shape == (m, 3)
    for key in ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1"):
        assert a[key].shape == ()


@pytest.mark.parametrize("name, scheme", CASE_SCHEMES)
def test_reference_cuts_are_consistent(name: str, scheme: str) -> None:
    _, mesh = load_mesh(name)
    a = load_scheme(name, scheme)
    alpha = mesh["alpha"][a["cells"]]
    assert np.all((alpha > TOL) & (alpha < 1 - TOL))
    # the reconstructed plane cuts the cell's alpha; isoAlpha's iso face is planar on
    # prisms and tetrahedra, not on hexahedra (bilinear point interpolation)
    if (name, scheme) != ("curvature3D", "isoAlpha"):
        np.testing.assert_allclose(a["plane_alpha"][:, 0], alpha, rtol=0, atol=TOL)
        np.testing.assert_allclose(a["plane_face_area"][:, 0], a["normal"], atol=1e-14)
    # planes 5 and 6 miss the cell
    assert np.all(a["plane_status"][:, 5] == 1) and np.all(a["plane_alpha"][:, 5] == 0)
    assert np.all(a["plane_status"][:, 6] == -1) and np.all(a["plane_alpha"][:, 6] == 1)
    # vofCutCell meets its targets; target 0 is the cell's alpha
    np.testing.assert_array_equal(a["sd_alpha_target"][:, 0], alpha)
    np.testing.assert_allclose(a["sd_alpha"], a["sd_alpha_target"], rtol=0, atol=TOL)
    volumes = mesh["cell_volumes"][a["cells"], None]
    np.testing.assert_allclose(a["sd_alpha"], a["sd_sub_volume"] / volumes, rtol=1e-12)
    # the unit plane normals
    np.testing.assert_allclose(np.linalg.norm(a["plane_normal"], axis=2), 1.0, rtol=1e-14)


@pytest.mark.geometricvof
@pytest.mark.parametrize("name", NAMES)
def test_rerun_reproduces_stored_reference(name: str, tmp_path: Path) -> None:
    if not have_openfoam():
        pytest.skip("OpenFOAM-v2406 not found ($OPENFOAM_BASHRC)")
    mesh_arrays, schemes = read_output(run_reference(name, tmp_path / name))
    _, stored_mesh = load_mesh(name)
    for key, value in mesh_arrays.items():
        np.testing.assert_array_equal(value, stored_mesh[key], err_msg=f"{name}: {key}")
    for scheme, arrays in schemes.items():
        stored = load_scheme(name, scheme)
        assert arrays.keys() == stored.keys()
        for key, value in arrays.items():
            np.testing.assert_array_equal(value, stored[key], err_msg=f"{name} {scheme}: {key}")
