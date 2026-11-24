"""The per-case metrics table and collect's merge of a case's tables on small tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.workflow import collect, metrics, read_table


def test_metrics_table_round_trips_and_prunes_the_inner_time_directories(
    tmp_path: Path,
) -> None:
    benchmark, case = tmp_path / "benchmark", tmp_path / "cases" / "n20_Serial"
    benchmark.mkdir()
    (benchmark / "benchmark.yaml").write_text("metrics: {script: metrics.py, prune: true}\n")
    (benchmark / "metrics.py").write_text(
        "import pandas as pd\n"
        "from neofoam_tutorials.suite.workflow import time_directories\n"
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


def test_collect_merges_the_tables_on_the_time_and_writes_the_histories(tmp_path: Path) -> None:
    benchmark, workdir = tmp_path / "benchmark", tmp_path / "run"
    benchmark.mkdir()
    (benchmark / "benchmark.yaml").write_text(
        "dimensions: {mesh: {n20: {}, n40: {}}}\n"
        "collect:\n"
        "  tables: [postProcessing/timing.dat, postProcessing/maxU.csv]\n"
        "  derive: metrics.py\n"
        "  history: true\n"
    )
    (benchmark / "metrics.py").write_text(
        "def derive(history, case):\n    return history.assign(maxU_max=history['maxU'].cummax())\n"
    )
    workdir.mkdir()
    (workdir / "sweep.csv").write_text("case,mesh\nn40,n40\nn20,n20\n")
    for case, scale in (("n20", 1.0), ("n40", 2.0)):
        post = workdir / "cases" / case / "postProcessing"
        post.mkdir(parents=True)
        # the accumulated end time of a .dat and the CSV's 12 digits are one time
        (post / "timing.dat").write_text("# Time wall_s\n0.30000000000000004 3.5\n")
        # a postProcess table, "-GREAT" (an empty selection) read as NaN
        (post / "maxU.csv").write_text(f"time,maxU\n0.1,{2 * scale}\n0.2,-1e+15\n0.3,{scale}\n")

    collect(benchmark, workdir, workdir / "results.csv")

    results = pd.read_csv(workdir / "results.csv", float_precision="round_trip")
    assert list(results["case"]) == ["n20", "n40"]
    assert list(results.columns) == ["case", "mesh", "Time", "wall_s", "maxU", "maxU_max"]
    assert results[["Time", "wall_s", "maxU", "maxU_max"]].values.tolist() == [
        [0.3, 3.5, 1.0, 2.0],
        [0.3, 3.5, 2.0, 4.0],
    ]
    history = pd.read_csv(workdir / "histories.csv", float_precision="round_trip")
    n40 = history[history["case"] == "n40"]
    assert n40["Time"].tolist() == [0.1, 0.2, 0.3] and n40["maxU"].isna().tolist() == [
        False,
        True,
        False,
    ]
    assert history["wall_s"].count() == 2
