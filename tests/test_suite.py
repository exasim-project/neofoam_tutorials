"""The benchmark suite on the circle benchmark's files: the swept variants of a smoke or
``--method`` run, and the checks of ``benchmark.yaml`` on the stored TwoPhaseFlow table;
the maximum, agreement and reference checks and the per-case metrics table on small
tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_verification.suite.benchmark import dimensions, load, name
from neofoam_verification.suite.checks import evaluate
from neofoam_verification.suite.workflow import metrics, read_table

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


def test_metrics_table_round_trips_and_prunes_the_inner_time_directories(
    tmp_path: Path,
) -> None:
    benchmark, case = tmp_path / "benchmark", tmp_path / "cases" / "n20_Serial"
    benchmark.mkdir()
    (benchmark / "benchmark.yaml").write_text("metrics: {script: metrics.py, prune: true}\n")
    (benchmark / "metrics.py").write_text(
        "import pandas as pd\n"
        "from neofoam_verification.suite.workflow import time_directories\n"
        "def metrics(case):\n"
        "    times = [float(t.name) for t in time_directories(case)]\n"
        "    return pd.DataFrame({'Time': times, 'maxU': [2 * t for t in times]})\n"
    )
    for time in ("0", "0.5", "1", "1.5", "constant"):
        (case / time).mkdir(parents=True)
    out = case / "postProcessing" / "metrics.dat"

    metrics(benchmark, case, out)

    assert read_table(out).to_dict("list") == {"Time": [0, 0.5, 1, 1.5], "maxU": [0, 1, 2, 3]}
    assert sorted(p.name for p in case.iterdir()) == ["0", "1.5", "constant", "postProcessing"]
