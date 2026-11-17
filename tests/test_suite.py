"""The benchmark suite on the circle benchmark's files: the swept variants of a smoke or
``--method`` run, and the checks of ``benchmark.yaml`` on the stored TwoPhaseFlow table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_verification.suite.benchmark import dimensions, load, name
from neofoam_verification.suite.checks import evaluate

CIRCLE = Path(__file__).resolve().parents[1] / "benchmarks" / "reconstruction" / "circle"
SPEC = load(CIRCLE)


def test_smoke_method_run_sweeps_the_smoke_variants_and_the_method() -> None:
    dims = dimensions(SPEC, smoke=True, methods=["myScheme"])

    assert name(CIRCLE) == "reconstruction/circle"
    assert list(dims["mesh"]) == ["n8", "n16"]
    assert dims["neo_n_control_config"] == {"Serial": {"executor": "Serial"}}
    assert dims["reconstruction_scheme_config"] == {
        "myScheme": {"reconstructionScheme": "myScheme"}
    }


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
