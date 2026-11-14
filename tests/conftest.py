"""Fixtures: one TwoPhaseFlow C++ MULES run per benchmark per session (about 3 s for
discUniFlow), shared by the metric validation and the reference regression."""

from __future__ import annotations

from pathlib import Path

import pytest

from neofoam_verification.backend import RunResult
from neofoam_verification.benchmarks import BENCHMARKS
from neofoam_verification.reference import have_twophaseflow, run_twophaseflow


@pytest.fixture(scope="session")
def twophaseflow_runs(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, tuple[RunResult, Path]]:
    if not have_twophaseflow():
        pytest.skip("TwoPhaseFlow's advectorVoF not found ($TWOPHASEFLOW_BASHRC)")
    runs = {}
    for name, benchmark in BENCHMARKS.items():
        case = tmp_path_factory.mktemp(name) / name
        result, _ = run_twophaseflow(benchmark, case)
        runs[name] = (result, case)
    return runs
