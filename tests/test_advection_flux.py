"""The stored isoAdvection face-flux reference (reference/curvature*/advection/).

Without OpenFOAM: the stored files load with the documented shapes, the inputs are
those of the reconstruction reference and the prescribed velocity, and every assembled
array follows from the unit-level rows (bitwise where OpenFOAM's arithmetic is a
single expression). With OpenFOAM-v2406 (marked ``geometricvof``): a rerun of the
utility reproduces the stored arrays bitwise.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from neofoam_tutorials import reconstruction
from neofoam_tutorials.advection_flux import (
    load_run,
    read_output,
    run_key,
    run_reference,
    runs,
    settings,
)
from neofoam_tutorials.reconstruction import NAMES, have_openfoam, load_mesh

RUNS = [(n, s, v, co) for n in NAMES for s, v, _, co in runs(n)]
IDS = [f"{n}-{run_key(s, v, co)}" for n, s, v, co in RUNS]
SMALL = 1e-15


def velocity(spec: Any, x: Any) -> Any:
    if spec["type"] == "uniform":
        return np.broadcast_to(np.asarray(spec["value"], dtype=float), x.shape)
    axis = np.asarray(spec["axis"], dtype=float)
    axis = axis / np.linalg.norm(axis)
    return float(spec["omega"]) * np.cross(axis, x - np.asarray(spec["origin"], dtype=float))


@pytest.fixture(params=RUNS, ids=IDS)
def run(request: pytest.FixtureRequest) -> tuple[str, str, str, dict[str, Any]]:
    name, scheme, vel, co = request.param
    return name, scheme, vel, load_run(name, scheme, vel, co)


def test_reference_has_the_documented_shapes(run: Any) -> None:
    name, _, _, a = run
    mesh, m_arrays = load_mesh(name)
    f, n, p = len(mesh.faces), len(m_arrays["alpha"]), len(mesh.points)
    m, r = len(a["cells"]), len(a["flux_face"])
    k = int(a["flux_n_points"].max())
    assert m > 0 and r > 0
    for key in ("dt", "courant", "max_courant"):
        assert a[key].shape == ()
    for key in ("face_patch", "face_empty", "mag_sf", "phi", "dVf_upwind", "dVf"):
        assert a[key].shape == (f,), key
    for key in ("isoadvected", "dVf_limited", "alpha_phi"):
        assert a[key].shape == (f,), key
    assert a["U"].shape == (n, 3) and a["U_boundary"].shape == (f, 3)
    assert a["U_points"].shape == (p, 3)
    for key in ("alpha0", "alpha_unbounded", "alpha"):
        assert a[key].shape == (n,), key
    for key in ("normal", "centre", "n0"):
        assert a[key].shape == (m, 3), key
    assert a["Un0"].shape == (m,)
    for key in ("flux_x0", "flux_n0"):
        assert a[key].shape == (r, 3), key
    for key in ("cell", "interface", "face", "boundary", "Un0", "dt", "phi", "mag_sf"):
        assert a[f"flux_{key}"].shape == (r,), key
    for key in ("branch", "n_shifts", "n_points", "dVf", "area", "alpha_f", "n_steps"):
        assert a[f"flux_{key}"].shape == (r,), key
    assert a["flux_p_times"].shape == (r, k)
    for key in ("kind", "t0", "t1", "area0", "alpha", "beta", "contribution"):
        assert a[f"step_{key}"].shape == (r, k + 2), key


def test_inputs_are_the_prescribed_velocity_and_reconstruction(run: Any) -> None:
    name, scheme, vel, a = run
    mesh, m_arrays = load_mesh(name)
    spec = settings(name)["velocities"][vel]
    np.testing.assert_array_equal(a["alpha0"], m_arrays["alpha"])
    # the interface of advect's reconstruct() is the reconstruction reference's
    rec = reconstruction.load_scheme(name, scheme)
    for key in ("cells", "normal", "centre"):
        np.testing.assert_array_equal(a[key], rec[key], err_msg=key)
    n0 = -a["normal"] / np.linalg.norm(a["normal"], axis=1)[:, None]
    np.testing.assert_allclose(a["n0"], n0, rtol=0, atol=1e-15)
    # U and phi = U(Cf) . Sf, nan on empty faces
    empty = a["face_empty"]
    assert np.all(np.isnan(a["phi"][empty])) and not np.any(np.isnan(a["phi"][~empty]))
    np.testing.assert_allclose(a["U"], velocity(spec, m_arrays["cell_centres"]), atol=1e-14)
    phi = np.einsum("ij,ij->i", velocity(spec, mesh.face_centres), mesh.face_areas)
    np.testing.assert_allclose(a["phi"][~empty], phi[~empty], rtol=0, atol=1e-15)
    boundary = ~empty & (a["face_patch"] >= 0)
    np.testing.assert_allclose(
        a["U_boundary"][boundary], velocity(spec, mesh.face_centres[boundary]), atol=1e-14
    )
    assert np.all(np.isnan(a["U_boundary"][~boundary]))
    np.testing.assert_allclose(a["max_courant"], a["courant"], rtol=1e-14)
    assert np.all(a["flux_dt"] == a["dt"])


def test_upwind_flux_is_openfoams_interpolation(run: Any) -> None:
    name, _, _, a = run
    mesh, _ = load_mesh(name)
    n_int = len(mesh.neighbour)
    alpha, phi, dt = a["alpha0"], a["phi"], a["dt"]
    own, nei = alpha[mesh.owner[:n_int]], alpha[mesh.neighbour]
    w = (phi[:n_int] >= 0).astype(float)
    np.testing.assert_array_equal(
        a["dVf_upwind"][:n_int], phi[:n_int] * (w * (own - nei) + nei) * dt
    )
    # zeroGradient alpha on the boundary
    np.testing.assert_array_equal(
        a["dVf_upwind"][n_int:], phi[n_int:] * alpha[mesh.owner[n_int:]] * dt
    )


def test_traced_faces_are_the_downwind_faces_of_the_surface_cells(run: Any) -> None:
    name, _, _, a = run
    mesh, _ = load_mesh(name)
    n_int = len(mesh.neighbour)
    i = a["flux_interface"]
    np.testing.assert_array_equal(a["flux_cell"], a["cells"][i])
    for key in ("x0", "n0", "Un0"):
        source = a["centre"] if key == "x0" else a[key]
        np.testing.assert_array_equal(a[f"flux_{key}"], source[i], err_msg=key)
    face = a["flux_face"]
    np.testing.assert_array_equal(a["flux_phi"], a["phi"][face])
    np.testing.assert_array_equal(a["flux_mag_sf"], a["mag_sf"][face])
    np.testing.assert_array_equal(a["flux_boundary"], face >= n_int)
    np.testing.assert_array_equal(a["flux_n_points"], [len(mesh.faces[fi]) for fi in face])
    # every face is traced once, and they are all the downwind faces of the surface cells
    assert len(set(face)) == len(face)
    expected = set()
    for celli in a["cells"]:
        for fi in mesh.cells[celli]:
            if a["face_empty"][fi]:
                continue
            upwind_owner = a["phi"][fi] >= 0
            if (mesh.owner[fi] == celli) == upwind_owner:
                expected.add(fi)
    assert set(face) == expected
    # the assembled face flux before bounding
    np.testing.assert_array_equal(a["isoadvected"], np.isin(np.arange(len(a["phi"])), face))
    np.testing.assert_array_equal(a["dVf"][face], a["flux_dVf"])
    keep = ~a["isoadvected"]
    np.testing.assert_array_equal(a["dVf"][keep], a["dVf_upwind"][keep])


def test_unit_results_follow_from_the_trace(run: Any) -> None:
    name, _, _, a = run
    mesh, _ = load_mesh(name)
    branch = a["flux_branch"]
    assert set(branch) <= {0, 1}, "branches 2 and 3 do not occur on these planar meshes"
    one = branch == 1
    np.testing.assert_array_equal(
        a["flux_dVf"][one], a["flux_phi"][one] / a["flux_mag_sf"][one] * a["flux_area"][one]
    )
    zero = branch == 0
    np.testing.assert_array_equal(
        a["flux_dVf"][zero], a["flux_phi"][zero] * a["dt"] * a["flux_alpha_f"][zero]
    )
    for r in np.flatnonzero(one):
        n_steps = a["flux_n_steps"][r]
        assert n_steps > 0 and np.all(a["step_kind"][r, n_steps:] == -1)
        area = 0.0
        for c in a["step_contribution"][r, :n_steps]:
            area += c
        assert area == a["flux_area"][r], r
        # the steps cover [0, dt] in order, up to the vertex times that
        # timeIntegratedArea drops within tSmall of the previous one (a step of kind 5
        # starts at the last vertex time, not at the last kept one)
        t0, t1 = a["step_t0"][r, :n_steps], a["step_t1"][r, :n_steps]
        t_small = max(1e-6 * a["dt"], 10 * SMALL)
        assert t0[0] == 0 and t1[-1] == a["dt"]
        assert np.all(np.abs(t0[1:] - t1[:-1]) <= t_small)
        # arrival times ((p - x0) . n0)/Un0
        n_points = a["flux_n_points"][r]
        p = mesh.points[mesh.faces[a["flux_face"][r]]]
        times = (p - a["flux_x0"][r]) @ a["flux_n0"][r] / a["flux_Un0"][r]
        times[np.abs(times) < 10 * SMALL] = 0
        np.testing.assert_allclose(a["flux_p_times"][r, :n_points], times, rtol=1e-13, atol=1e-14)
    # the swept volume is at most the face's flux
    face = a["flux_face"]
    assert np.all(np.abs(a["flux_dVf"]) <= np.abs(a["phi"][face]) * a["dt"] * (1 + 1e-12))
    assert np.all(np.sign(a["flux_dVf"]) * np.sign(a["flux_phi"]) >= 0)


def test_advected_alpha_follows_from_the_face_fluxes(run: Any) -> None:
    name, _, _, a = run
    mesh, m_arrays = load_mesh(name)
    volumes = m_arrays["cell_volumes"]
    n_int = len(mesh.neighbour)

    def net(dVf: Any) -> Any:
        out = np.zeros(len(volumes))
        np.add.at(out, mesh.owner, np.nan_to_num(dVf))
        np.add.at(out, mesh.neighbour, -dVf[:n_int])
        return out / volumes

    np.testing.assert_allclose(
        a["alpha_unbounded"], a["alpha0"] - net(a["dVf"]), rtol=0, atol=1e-13
    )
    assert np.all((a["alpha"] >= 0) & (a["alpha"] <= 1))
    np.testing.assert_allclose(a["dVf_limited"], a["alpha_phi"] * a["dt"], rtol=1e-14, atol=1e-20)
    np.testing.assert_allclose(
        np.clip(a["alpha0"] - net(a["dVf_limited"]), 0, 1), a["alpha"], rtol=0, atol=1e-12
    )


@pytest.mark.geometricvof
@pytest.mark.parametrize("name", NAMES)
def test_rerun_reproduces_stored_reference(name: str, tmp_path: Path) -> None:
    if not have_openfoam():
        pytest.skip("OpenFOAM-v2406 not found ($OPENFOAM_BASHRC)")
    arrays = read_output(name, run_reference(name, tmp_path / name))
    for scheme, vel, _, co in runs(name):
        stored = load_run(name, scheme, vel, co)
        new = arrays[run_key(scheme, vel, co)]
        assert new.keys() == stored.keys()
        for key, value in new.items():
            np.testing.assert_array_equal(
                value, stored[key], err_msg=f"{name} {run_key(scheme, vel, co)}: {key}"
            )
