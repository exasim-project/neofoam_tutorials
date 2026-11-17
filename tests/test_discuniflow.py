"""The discUniFlow benchmarks' files: the smoke variants, and the checks of their
``benchmark.yaml`` on the stored reference tables (numufoam, TwoPhaseFlow)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_verification.suite.benchmark import dimensions, load
from neofoam_verification.suite.checks import evaluate

ADVECTION = Path(__file__).resolve().parents[1] / "benchmarks" / "advection"
PAPER = ADVECTION / "discUniFlow"
TESTSUITE = ADVECTION / "discUniFlowTestsuite"


def _as_results(stored: pd.DataFrame) -> pd.DataFrame:
    """A stored table as the Serial rows of a ``results.csv``."""
    return stored.assign(
        case=[f"{m}_{c}" for m, c in zip(stored["method"], stored.get("CFL", stored["mesh"]))],
        executor="Serial",
    )


def test_smoke_run_sweeps_the_coarsest_mesh_one_cfl_serial_and_both_methods() -> None:
    dims = dimensions(load(PAPER), smoke=True)

    assert list(dims["mesh"]) == ["n10"]
    assert dims["control_dict_config"] == {"CFL01": {"maxAlphaCo": 0.1}}
    assert list(dims["neo_n_control_config"]) == ["Serial"]
    assert list(dims["advection_scheme_config"]) == ["isoAdvector", "MULES"]


def test_numufoam_mules_passes_the_checks_and_where_limits_the_bound_check() -> None:
    stored = pd.read_csv(PAPER / "reference" / "numufoam.csv")
    mules = _as_results(stored[stored["method"] == "MULES"])

    results = evaluate(
        load(PAPER)["checks"], mules, PAPER / "reference", ["CFL", "executor", "method"]
    )

    statuses = {(r["check"], r["group"]): r["status"] for r in results}
    assert set(statuses.values()) == {"pass"}, results
    for cfl in ("CFL005", "CFL01", "CFL02", "CFL05"):
        reference = [
            s
            for (c, g), s in statuses.items()
            if c.startswith("reference numufoam.csv") and g == f"{cfl} Serial MULES"
        ]
        assert reference == ["pass"]
    # numufoam's MULES overshoots at CFL 0.2 and 0.5: not held to the bound
    bounded = {g for c, g in statuses if c == "maximum Ebound"}
    assert bounded == {"CFL005 Serial MULES", "CFL01 Serial MULES"}


def test_maximum_check_fails_above_its_bound() -> None:
    stored = pd.read_csv(PAPER / "reference" / "numufoam.csv")
    mules = _as_results(stored[(stored["method"] == "MULES") & (stored["CFL"] == "CFL05")])
    check = {"type": "maximum", "column": "Ebound", "maximum": 1e-8}

    (result,) = evaluate([check], mules, PAPER / "reference", ["CFL", "executor", "method"])

    assert result["status"] == "fail"
    assert result["detail"].startswith("1.161e-01")


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
