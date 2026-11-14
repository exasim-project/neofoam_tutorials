"""The stored OpenFOAM MULES reference (reference/<case>/) is what TwoPhaseFlow's
advectorVoF produces today: same binary, same inputs, so the final alpha agrees to the
17 written digits and the metrics to round-off (Emass is round-off itself).

The MULES metrics are reported, not held against TwoPhaseFlow's testsuite limits,
which are tuned for isoAdvector/plicRDF (discUniFlow: Eshape <= 0.0122).
"""

from __future__ import annotations

import numpy as np

from neofoam_verification.benchmarks import BENCHMARKS
from neofoam_verification.foam import read_function_object_dat
from neofoam_verification.reference import DAT, load_reference


def test_rerun_reproduces_stored_reference(twophaseflow_runs) -> None:  # type: ignore[no-untyped-def]
    for name, (result, case) in twophaseflow_runs.items():
        ref_rows, ref_alpha = load_reference(BENCHMARKS[name])
        rows = read_function_object_dat(case / DAT)
        np.testing.assert_allclose(result.alpha[-1], ref_alpha, rtol=0, atol=1e-15, err_msg=name)
        np.testing.assert_allclose(
            rows[:, 1], ref_rows[:, 1], rtol=1e-12, err_msg=f"{name}: Eshape"
        )
        np.testing.assert_allclose(rows[:, 2:4], ref_rows[:, 2:4], rtol=0, atol=1e-15, err_msg=name)
