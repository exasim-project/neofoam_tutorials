"""NeoFOAM's MULES advection (through backend.run_case) against the stored OpenFOAM
MULES reference: final alpha matches, Eshape and Ebound match the reference's at every
write time, mass is conserved and, where the reference is bounded, alpha stays in [0, 1].

The reference is TwoPhaseFlow's MULESScheme on OpenFOAM-v2506; the library runs
OpenFOAM-v2406 MULES (openfoam) or NeoN's kernels (neon). advectorVoF also adds the
source div(phi) min(alpha, 1), round-off for these divergence-free fluxes, which the
library does not have. Eshape = sum V |alpha - alphaExact| moves by at most
ALPHA_ATOL times the domain volume when alpha moves by ALPHA_ATOL; Ebound is a max of
alpha's excursions, so it moves by at most ALPHA_ATOL.

vortexShearedDisc's final field is ill-conditioned under MULES: the C++ reference itself
answers a 1e-14 relative change of the initial alpha with a change of 4.3e-5 at t = 8
(8e-9 at t = 4, where the flow turns), in the few hundred filament cells with alpha ~1e-4
(README). Its final-field tolerance is that measured response rounded up to 1e-4; its
Eshape and Ebound still hold the ALPHA_ATOL-derived tolerances (measured: 1e-11).

MULES with the testsuite's nAlphaCorr 2 is not bounded in the deforming flows: the
reference itself leaves [0, 1] by up to 6e-3 there (README), so only discUniFlow is held
to BOUND_ATOL; the others have to reproduce the reference's Ebound.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neofoam_tutorials.backend import run_case
from neofoam_tutorials.benchmarks import BENCHMARKS, Benchmark
from neofoam_tutorials.reference import evaluate, have_twophaseflow, load_reference, mesh_case

ALPHA_ATOL = 1e-10  # final alpha vs the OpenFOAM MULES reference
MASS_RTOL = 1e-12  # Emass / initial mass
BOUND_ATOL = 1e-12  # Ebound

CONFIGS = [("openfoam", "Serial"), ("neon", "Serial"), ("neon", "CPU"), ("neon", "GPU")]
BOUNDED_REFERENCE = ("discUniFlow",)
FINAL_ALPHA_ATOL = {"vortexShearedDisc": 1e-4}  # see the module docstring


@pytest.mark.backend
@pytest.mark.parametrize("backend, executor", CONFIGS, ids=[f"{b}-{e}" for b, e in CONFIGS])
@pytest.mark.parametrize("benchmark", BENCHMARKS.values(), ids=BENCHMARKS.keys())
def test_backend_matches_openfoam_mules_reference(
    benchmark: Benchmark, backend: str, executor: str, tmp_path: Path
) -> None:
    if not have_twophaseflow():
        pytest.skip("meshing the case needs blockMesh/setAlphaField ($TWOPHASEFLOW_BASHRC)")
    case = mesh_case(benchmark, tmp_path / benchmark.name)
    try:
        result = run_case(benchmark, backend, executor, case)
    except NotImplementedError as err:
        pytest.skip(str(err))

    ref_rows, ref_alpha = load_reference(benchmark)
    rows = evaluate(benchmark, result)
    initial_mass = float(np.sum(result.volumes * result.alpha[0]))
    domain_volume = float(np.sum(result.volumes))
    label = f"{benchmark.name} {backend}-{executor}"
    np.testing.assert_allclose(
        result.alpha[-1],
        ref_alpha,
        rtol=0,
        atol=FINAL_ALPHA_ATOL.get(benchmark.name, ALPHA_ATOL),
        err_msg=f"{label}: alpha",
    )
    np.testing.assert_allclose(
        rows[:, 1],
        ref_rows[:, 1],
        rtol=0,
        atol=ALPHA_ATOL * domain_volume,
        err_msg=f"{label}: Eshape",
    )
    np.testing.assert_allclose(
        rows[:, 3], ref_rows[:, 3], rtol=0, atol=ALPHA_ATOL, err_msg=f"{label}: Ebound"
    )
    np.testing.assert_array_less(rows[:, 2], MASS_RTOL * initial_mass, err_msg=f"{label}: Emass")
    if benchmark.name in BOUNDED_REFERENCE:
        np.testing.assert_array_less(rows[:, 3], BOUND_ATOL, err_msg=f"{label}: Ebound")
