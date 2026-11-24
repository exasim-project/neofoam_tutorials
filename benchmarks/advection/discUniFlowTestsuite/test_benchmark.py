"""The checks of the discUniFlowTestsuite benchmark's ``benchmark.yaml`` on the stored
TwoPhaseFlow tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.benchmark import load
from neofoam_tutorials.suite.checks import evaluate

TESTSUITE = Path(__file__).resolve().parent


def _as_results(stored: pd.DataFrame) -> pd.DataFrame:
    """A stored table as the Serial rows of a ``results.csv``."""
    return stored.assign(
        case=[f"{m}_{c}" for m, c in zip(stored["method"], stored.get("CFL", stored["mesh"]))],
        executor="Serial",
    )


def test_stored_twophaseflow_runs_pass_the_testsuite_checks() -> None:
    stored = pd.concat(
        pd.read_csv(TESTSUITE / "reference" / f"twophaseflow_{scheme}.csv")
        for scheme in ("mules", "isoadvection")
    )

    results = evaluate(
        load(TESTSUITE)["checks"],
        _as_results(stored),
        TESTSUITE / "reference",
        ["executor", "method"],
    )

    # the reference check's label is "reference <file> <columns>": key it by the file
    statuses = {(" ".join(r["check"].split()[:2]), r["group"]): r["status"] for r in results}
    assert statuses["reference twophaseflow_mules.csv", "Serial MULES"] == "pass"
    assert statuses["reference twophaseflow_mules.csv", "Serial isoAdvector"] == "skip"
    assert statuses["reference twophaseflow_isoadvection.csv", "Serial isoAdvector"] == "pass"
    assert {s for (c, _), s in statuses.items() if c.startswith("maximum")} == {"pass"}
