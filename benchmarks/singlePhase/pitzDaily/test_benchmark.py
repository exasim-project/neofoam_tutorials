"""The checks of the pitzDaily benchmark's ``benchmark.yaml`` on its stored OpenFOAM table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.benchmark import load
from neofoam_tutorials.suite.checks import evaluate

PITZ_DAILY = Path(__file__).resolve().parent


def test_stored_openfoam_table_passes_the_pitz_daily_reference_checks() -> None:
    stored = pd.read_csv(PITZ_DAILY / "reference" / "openfoam.csv")
    results = stored.assign(case=stored["mesh"] + "_Serial", executor="Serial")
    checks = [c for c in load(PITZ_DAILY)["checks"] if c.get("file") == "openfoam.csv"]

    out = evaluate(checks, results, PITZ_DAILY / "reference", ["executor"])

    assert len(out) == 2
    assert {c["status"] for c in out} == {"pass"}, out
