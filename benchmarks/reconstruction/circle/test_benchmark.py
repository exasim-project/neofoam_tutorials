"""The checks of the circle benchmark's ``benchmark.yaml`` on its stored TwoPhaseFlow table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.benchmark import load
from neofoam_tutorials.suite.checks import evaluate

CIRCLE = Path(__file__).resolve().parent
SPEC = load(CIRCLE)


def test_stored_twophaseflow_table_passes_the_checks() -> None:
    stored = pd.read_csv(CIRCLE / "reference" / "twophaseflow.csv")
    results = stored.assign(
        case=[f"n{n}_Serial_{m}" for n, m in zip(stored["resolution"], stored["method"])],
        executor="Serial",
        nCells=stored["nCells"].astype(float),
    )

    checks = evaluate(SPEC["checks"], results, CIRCLE / "reference", ["executor", "method"])

    assert len(checks) == 3
    assert {c["status"] for c in checks} == {"pass"}, checks
