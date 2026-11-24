"""The maximum, agreement and reference checks on small tables and on discUniFlow's stored
numufoam table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.checks import evaluate

PAPER = Path(__file__).resolve().parents[2] / "benchmarks" / "advection" / "discUniFlow"


def _as_results(stored: pd.DataFrame) -> pd.DataFrame:
    """A stored table as the Serial rows of a ``results.csv``."""
    return stored.assign(
        case=[f"{m}_{c}" for m, c in zip(stored["method"], stored.get("CFL", stored["mesh"]))],
        executor="Serial",
    )


def _executor_results(scale: dict[str, float]) -> pd.DataFrame:
    """Two meshes per executor, ``maxU`` scaled per executor."""
    return pd.DataFrame(
        [
            {"case": f"{m}_{e}", "mesh": m, "executor": e, "maxU": u * scale[e]}
            for e in scale
            for m, u in (("n20", 0.1), ("n40", 0.2))
        ]
    )


def test_maximum_bounds_each_executors_largest_value() -> None:
    results = _executor_results({"Serial": 1.0, "GPU": 2.0})
    check = {"type": "maximum", "column": "maxU", "maximum": 0.3}

    checks = evaluate([check], results, Path("."), ["executor"])

    assert [(c["group"], c["status"]) for c in checks] == [("GPU", "fail"), ("Serial", "pass")]
    assert "n40_GPU" in checks[0]["detail"]


def test_maximum_check_fails_above_its_bound() -> None:
    stored = pd.read_csv(PAPER / "reference" / "numufoam.csv")
    mules = _as_results(stored[(stored["method"] == "MULES") & (stored["CFL"] == "CFL05")])
    check = {"type": "maximum", "column": "Ebound", "maximum": 1e-8}

    (result,) = evaluate([check], mules, PAPER / "reference", ["CFL", "executor", "method"])

    assert result["status"] == "fail"
    assert result["detail"].startswith("1.161e-01")


def test_agreement_compares_each_executor_with_the_base_on_the_same_mesh() -> None:
    results = _executor_results({"CPU": 1.0 + 1e-12, "GPU": 1.0 + 1e-6, "Serial": 1.0})
    check = {"type": "agreement", "across": "executor", "base": "Serial", "columns": ["maxU"]}

    checks = evaluate([check | {"rtol": 1e-8}], results, Path("."), ["executor"])

    assert [(c["group"], c["status"]) for c in checks] == [
        ("CPU vs Serial", "pass"),
        ("GPU vs Serial", "fail"),
    ]


def test_reference_skips_empty_stored_values(tmp_path: Path) -> None:
    (tmp_path / "stored.csv").write_text("mesh,maxU\nn20,\nn40,0.2\n")
    results = _executor_results({"Serial": 1.0})
    check = {"type": "reference", "file": "stored.csv", "match": ["mesh"], "columns": ["maxU"]}

    checks = evaluate([check | {"rtol": 1e-12}], results, tmp_path, ["executor"])

    assert checks[0]["status"] == "pass"
    assert "n40_Serial" in checks[0]["detail"]
