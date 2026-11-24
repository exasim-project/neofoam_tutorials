"""The stored multi-step isoAdvection reference (reference/<case>/isoAdvection/).

Without OpenFOAM: the stored files load with the documented shapes and are
self-consistent (time steps, limitFluxes iterations, mass conservation up to the
clipping, alpha in [0, 1], step 1's fields from its face fluxes, the errors from the
stored alpha). With OpenFOAM-v2406 (marked ``geometricvof``; vortexShearedDisc also
needs TwoPhaseFlow for its mesh, marked ``openfoam``): a rerun reproduces the stored
arrays bitwise.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from neofoam_tutorials import isoadvection
from neofoam_tutorials.cut_cell import exact_alpha
from neofoam_tutorials.isoadvection import (
    RUNS,
    SCHEMES,
    exact_shape,
    load_run,
    load_twophaseflow,
    read_run,
    run_key,
    run_keys,
    run_reference,
    velocities,
    write_times,
)
from neofoam_tutorials.metrics import bound_error, mass_error, shape_error
from neofoam_tutorials.reconstruction import have_openfoam, load_mesh
from neofoam_tutorials.reference import have_twophaseflow

PARAMS = [(label, s, v) for label, case in RUNS.items() for s, v in run_keys(case)]
IDS = [f"{label}-{run_key(s, v)}" for label, s, v in PARAMS]
A_TOL = 100 * 1e-15  # limitFluxes' bound tolerance, 100 SMALL


@pytest.fixture(params=PARAMS, ids=IDS)
def run(request: pytest.FixtureRequest) -> tuple[str, str | None, dict[str, Any]]:
    label, scheme, velocity = request.param
    return label, velocity, load_run(label, scheme, velocity)


def test_reference_has_the_documented_shapes(run: Any) -> None:
    label, _, a = run
    s, n = len(a["dt"]), len(a["alpha0"])
    k, m = len(a["snapshot_steps"]), len(a["s1_cells"])
    f = len(a["s1_dVf_unlimited"])
    for key in isoadvection.STEP_COLUMNS[1:]:
        assert a[key].shape == (s,), key
    for key in ("n_iter", "surface_cells", "snapshot_steps", "s1_cells"):
        assert a[key].dtype == np.int64, key
    assert a["cell_volumes"].shape == (n,) and a["s1_alpha_unclipped"].shape == (n,)
    assert a["snapshot_time"].shape == (k,) and a["snapshot_alpha"].shape == (k, n)
    assert a["s1_alpha_bounds"].shape == (3, n) and a["s1_dVf_limited"].shape == (f,)
    for key in ("s1_normal", "s1_x0", "s1_n0"):
        assert a[key].shape == (m, 3), key
    assert a["s1_Un0"].shape == (m,)
    w = len(write_times(RUNS[label], run[1]))
    for key in ("write_time", "Eshape", "Emass", "Ebound"):
        assert a[key].shape == (w,), key
    if RUNS[label].store_inputs:
        assert a["s1_U"].shape == (n, 3) and a["s1_phi"].shape == (f,)
    else:
        assert "s1_U" not in a and "s1_phi" not in a


def test_time_steps_reach_the_write_times(run: Any) -> None:
    label, velocity, a = run
    np.testing.assert_allclose(a["time"], np.cumsum(a["dt"]), rtol=1e-12)
    assert np.all(a["dt"] > 0)
    times = write_times(RUNS[label], velocity)
    np.testing.assert_allclose(a["write_time"], times)
    assert a["time"][-1] == pytest.approx(times[-1], abs=1e-12)
    # alpha is stored after step 1 and at every write time
    assert a["snapshot_steps"][0] == 1
    for t in times:
        assert np.any(np.isclose(a["snapshot_time"], t, rtol=0, atol=1e-9)), t
    np.testing.assert_array_equal(a["snapshot_time"], a["time"][a["snapshot_steps"] - 1])


def test_limit_fluxes_iterations(run: Any) -> None:
    _, _, a = run
    assert set(a["n_iter"]) <= {0, 1, 2, 3}
    # limitFluxes stops once alpha is within [-aTol, 1 + aTol]
    stopped = a["n_iter"] < 3
    assert np.all(a["min_unclipped"][stopped] >= -A_TOL)
    assert np.all(a["max_unclipped"][stopped] <= 1 + A_TOL)
    # step 1: the iterations before the last left alpha unbounded
    bounds = a["s1_alpha_bounds"]
    n_iter = a["n_iter"][0]
    for j in range(n_iter):
        assert bounds[j].min() < -A_TOL or bounds[j].max() > 1 + A_TOL, j
    for j in range(n_iter, 3):
        np.testing.assert_array_equal(bounds[j], a["s1_alpha_unclipped"])


def test_mass_is_conserved_up_to_the_clipping(run: Any) -> None:
    _, _, a = run
    volumes = a["cell_volumes"]
    mass0 = np.sum(volumes * a["alpha0"])
    previous = np.concatenate([[mass0], a["mass"][:-1]])
    # the interface stays inside the domain: no flux of alpha through the boundary
    np.testing.assert_allclose(a["mass_unclipped"], previous, rtol=1e-13)
    # clipping removes at most the violation of the bounds in every cell
    violation = np.maximum(-a["min_unclipped"], a["max_unclipped"] - 1).clip(0)
    assert np.all(np.abs(a["mass"] - a["mass_unclipped"]) <= violation * volumes.sum() + 1e-16)
    assert np.all((a["min"] >= 0) & (a["max"] <= 1))


def test_stored_alpha_is_bounded_and_matches_the_step_table(run: Any) -> None:
    _, _, a = run
    alpha, volumes = a["snapshot_alpha"], a["cell_volumes"]
    assert np.all((alpha >= 0) & (alpha <= 1))
    i = a["snapshot_steps"] - 1
    np.testing.assert_allclose(alpha @ volumes, a["mass"][i], rtol=1e-13)
    np.testing.assert_array_equal(alpha.min(axis=1), a["min"][i])
    np.testing.assert_array_equal(alpha.max(axis=1), a["max"][i])
    # step 1 is clipped from its unclipped alpha
    np.testing.assert_array_equal(np.clip(a["s1_alpha_unclipped"], 0, 1), alpha[0])
    # a face flux is a volume of the step's fluid; total mass of step 1's updates
    mass0 = a["alpha0"] @ volumes
    for field in (a["s1_alpha_bounds"][0], a["s1_alpha_unclipped"]):
        assert field @ volumes == pytest.approx(mass0, rel=1e-13)


def test_interface_of_step_1(run: Any) -> None:
    label, velocity, a = run
    normal = a["s1_normal"]
    np.testing.assert_allclose(
        a["s1_n0"], -normal / np.linalg.norm(normal, axis=1)[:, None], rtol=0, atol=1e-15
    )
    alpha0 = a["alpha0"][a["s1_cells"]]
    assert np.all((alpha0 > 1e-8) & (alpha0 < 1 - 1e-8))
    assert a["surface_cells"][0] == len(a["s1_cells"])
    if "s1_U" in a:
        u = a["s1_U"]
        if np.ptp(u, axis=0).max() == 0:
            # interpolationCellPoint reproduces a uniform velocity
            np.testing.assert_allclose(a["s1_Un0"], a["s1_n0"] @ u[0], rtol=0, atol=1e-14)
        # the swept volume is at most the face's flux
        phi = a["s1_phi"]
        dt = a["dt"][0]
        ok = ~np.isnan(phi)
        assert np.all(np.abs(a["s1_dVf_unlimited"][ok]) <= np.abs(phi[ok]) * dt * (1 + 1e-12))


def test_step_1_alpha_follows_from_the_face_fluxes() -> None:
    mesh, m = load_mesh("curvature2D")
    n_int = len(mesh.neighbour)
    for scheme, velocity in run_keys(RUNS["curvature2D"]):
        a = load_run("curvature2D", scheme, velocity)
        np.testing.assert_array_equal(a["alpha0"], m["alpha"])
        np.testing.assert_array_equal(a["cell_volumes"], m["cell_volumes"])

        def update(dVf: Any) -> Any:
            out = np.zeros(mesh.n_cells)
            np.add.at(out, mesh.owner, np.nan_to_num(dVf))
            np.add.at(out, mesh.neighbour, -dVf[:n_int])
            return a["alpha0"] - out / a["cell_volumes"]

        np.testing.assert_allclose(
            a["s1_alpha_bounds"][0], update(a["s1_dVf_unlimited"]), rtol=0, atol=1e-13
        )
        np.testing.assert_allclose(
            a["s1_alpha_unclipped"], update(a["s1_dVf_limited"]), rtol=0, atol=1e-13
        )


def test_errors_follow_from_the_stored_alpha(run: Any) -> None:
    label, velocity, a = run
    volumes = a["cell_volumes"]
    mass0 = float(np.sum(volumes * a["alpha0"]))
    for j, t in enumerate(a["write_time"]):
        (i,) = np.flatnonzero(np.isclose(a["snapshot_time"], t, rtol=0, atol=1e-9))
        alpha = a["snapshot_alpha"][i]
        assert a["Emass"][j] == mass_error(alpha, volumes, mass0)
        assert a["Ebound"][j] == bound_error(alpha)
        if label == "curvature2D":
            mesh, _ = load_mesh(label)
            moved = exact_shape(RUNS[label], velocity, a["s1_U"], t)
            alpha_exact = exact_alpha(mesh, moved.value(mesh.points))
            assert a["Eshape"][j] == pytest.approx(
                shape_error(alpha, volumes, alpha_exact), rel=1e-12
            )


def test_rotation_moves_the_disc_by_the_angle() -> None:
    spec = velocities(RUNS["curvature2D"])["rotation"]
    shape = exact_shape(RUNS["curvature2D"], "rotation", None, np.pi / float(spec["omega"]))
    # half a turn mirrors the centre at the rotation origin (x-z plane)
    origin = np.asarray(spec["origin"], dtype=float)
    centre = 2 * origin - np.array([1.01, 0.0, 1.01])
    np.testing.assert_allclose(shape.origin, centre, atol=1e-14)


@pytest.mark.geometricvof
@pytest.mark.parametrize(
    "label", ["curvature2D", pytest.param("vortexShearedDisc/32x32", marks=pytest.mark.openfoam)]
)
def test_rerun_reproduces_stored_reference(label: str, tmp_path: Path) -> None:
    if not have_openfoam():
        pytest.skip("OpenFOAM-v2406 not found ($OPENFOAM_BASHRC)")
    case = RUNS[label]
    if case.resolution is not None and not have_twophaseflow():
        pytest.skip("TwoPhaseFlow's setAlphaField not found ($TWOPHASEFLOW_BASHRC)")
    case_dir, _ = run_reference(case, tmp_path / case.name)
    for scheme, velocity in run_keys(case):
        stored = load_run(label, scheme, velocity)
        new = read_run(case_dir, scheme, velocity)
        assert set(new) <= set(stored)
        for key, value in new.items():
            np.testing.assert_array_equal(
                value, stored[key], err_msg=f"{label} {run_key(scheme, velocity)}: {key}"
            )


TWOPHASEFLOW = [
    (label, s) for label, case in RUNS.items() if case.resolution is not None for s in SCHEMES
]


@pytest.mark.parametrize("label, scheme", TWOPHASEFLOW, ids=[f"{lb}-{s}" for lb, s in TWOPHASEFLOW])
def test_twophaseflow_isoadvection_matches_the_v2406_run(label: str, scheme: str) -> None:
    """advectorVoF with TwoPhaseFlow's isoAdvection (v2506, Su = div(phi0) min(alpha, 1))
    agrees with the v2406 parity run to round-off amplified over the run."""
    dat, alpha = load_twophaseflow(label, scheme)
    a = load_run(label, scheme)
    np.testing.assert_allclose(dat[:, 0], a["write_time"])
    np.testing.assert_allclose(dat[:, 1], a["Eshape"], rtol=1e-10)
    assert np.all((alpha >= 0) & (alpha <= 1))
    np.testing.assert_allclose(alpha, a["snapshot_alpha"][-1], rtol=0, atol=1e-9)
