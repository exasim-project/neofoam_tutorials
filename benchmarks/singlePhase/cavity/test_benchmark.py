"""The checks of the cavity benchmark's ``benchmark.yaml`` on its stored icoFoam table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.benchmark import load
from neofoam_tutorials.suite.checks import evaluate

CAVITY = Path(__file__).resolve().parent


def test_stored_icofoam_table_passes_the_cavity_reference_and_order_checks() -> None:
    stored = pd.read_csv(CAVITY / "reference" / "icofoam.csv")
    results = stored.assign(
        case=stored["mesh"] + "_Serial", executor="Serial", h=1 / stored["mesh"].str[1:].astype(int)
    )
    checks = [c for c in load(CAVITY)["checks"] if c["type"] in ("reference", "order")]

    out = evaluate(checks, results, CAVITY / "reference", ["executor"])

    assert len(out) == 2
    assert {c["status"] for c in out} == {"pass"}, out
