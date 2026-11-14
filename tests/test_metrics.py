"""The Python volumeFractionError against TwoPhaseFlow's C++ function object.

Both evaluate the same written alpha fields of one advectorVoF run (written with 17
digits): Eshape agrees to round-off of a sum over the cells; Ebound is a min/max and
agrees exactly; Emass is itself round-off (~1e-16 of a volume of 0.19), so it agrees
to a few ulps of the total volume: 16 at discUniFlow's 6000 cells, growing linearly
with the number of cells as the worst-case error of the C++ sequential sum does
(deformationSphere, 65536 cells: 7.6e-17 of 0.014); the mesh measures are sums the
C++ accumulates sequentially (numpy: pairwise), 1e-12.
"""

from __future__ import annotations

import numpy as np

from neofoam_verification.benchmarks import BENCHMARKS
from neofoam_verification.foam import PolyMesh, read_function_object_dat
from neofoam_verification.metrics import mesh_measures
from neofoam_verification.reference import DAT, evaluate


def test_python_metrics_match_cpp_volumeFractionError(twophaseflow_runs) -> None:  # type: ignore[no-untyped-def]
    for name, (result, case) in twophaseflow_runs.items():
        cpp = read_function_object_dat(case / DAT)
        py = evaluate(BENCHMARKS[name], result)
        initial_mass = float(np.sum(result.volumes * result.alpha[0]))
        np.testing.assert_array_equal(py[:, 0], cpp[:, 0], err_msg=f"{name}: write times")
        np.testing.assert_allclose(py[:, 1], cpp[:, 1], rtol=1e-12, err_msg=f"{name}: Eshape")
        np.testing.assert_allclose(
            py[:, 2],
            cpp[:, 2],
            rtol=0,
            atol=16 * np.finfo(float).eps * initial_mass * max(1.0, len(result.volumes) / 6000),
            err_msg=f"{name}: Emass",
        )
        np.testing.assert_array_equal(py[:, 3], cpp[:, 3], err_msg=f"{name}: Ebound")


def test_python_mesh_measures_match_cpp(twophaseflow_runs) -> None:  # type: ignore[no-untyped-def]
    for name, (result, case) in twophaseflow_runs.items():
        cpp = read_function_object_dat(case / DAT)[0]
        measures = mesh_measures(PolyMesh.read(case))
        np.testing.assert_allclose(
            [measures["celltoCellDist"], measures["Ncells"], measures["avgCellVol"]],
            cpp[6:9],
            rtol=1e-12,
            err_msg=name,
        )


def test_initial_alpha_is_the_exact_volume_fraction(twophaseflow_runs) -> None:  # type: ignore[no-untyped-def]
    """setAlphaField (OpenFOAM) and the Python cut cell agree on the initial field."""
    from neofoam_verification.foam import read_internal_field
    from neofoam_verification.metrics import exact_alpha_at

    for name, (result, case) in twophaseflow_runs.items():
        b = BENCHMARKS[name]
        mesh = PolyMesh.read(case)
        velocity = read_internal_field(case / "0" / "U", mesh.n_cells)
        exact = exact_alpha_at(mesh, b.shape, velocity, 0.0)
        np.testing.assert_allclose(result.alpha[0], exact, rtol=0, atol=1e-14, err_msg=name)
