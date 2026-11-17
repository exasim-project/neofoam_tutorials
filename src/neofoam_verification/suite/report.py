"""``report.md`` of one benchmark run and ``results/summary.md`` over all of them."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .benchmark import Benchmark
from .checks import Result, read_table
from .plots import plot_name


def _row(cells: Sequence[object]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return [_row(header), _row(["---"] * len(header)), *(_row(r) for r in rows), ""]


def write_report(benchmark: Benchmark, workdir: Path, results: Sequence[Result], out: Path) -> None:
    run = json.loads((workdir / "run.json").read_text())
    checks = json.loads((workdir / "checks.json").read_text())["checks"]
    columns = list(benchmark.report_columns or benchmark.table.columns)
    methods = sorted({case["method"] for case in run["cases"]})
    lines = [
        f"# {benchmark.name}",
        "",
        f"Solver `{benchmark.solver}`; {'smoke' if run['smoke'] else 'full'} sweep; "
        f"methods {', '.join(methods)}; backends {', '.join(run['backends']) or 'none'}.",
        "",
    ]
    for backend, reason in run["skipped"].items():
        lines += [f"**{backend}: skipped** -- {reason}", ""]
    lines += ["All results: [results.csv](results.csv).", ""]
    for plot in benchmark.plots:
        name = plot_name(plot)
        lines += [f"![{name}](plots/{name}.png) ([pdf](plots/{name}.pdf))", ""]
    for backend in run["backends"]:
        rows = sorted(
            (r for r in results if r.backend == backend), key=lambda r: (r.method, r.resolution)
        )
        lines += [f"## {backend}", ""]
        lines += _table(
            ["method", "n", *columns, "wall [s]"],
            [
                [
                    r.method,
                    r.resolution,
                    *(f"{r.values[c]:.4e}" for c in columns),
                    f"{r.values['wall_s']:.2f}",
                ]
                for r in rows
            ],
        )
        lines += ["Observed order between consecutive resolutions:", ""]
        order_rows = []
        for method in methods:
            group = [r for r in rows if r.method == method]
            for coarse, fine in zip(group, group[1:]):
                ratio = coarse.values[benchmark.spacing] / fine.values[benchmark.spacing]
                order_rows.append(
                    [method, f"{coarse.resolution} -> {fine.resolution}"]
                    + [
                        f"{np.log(coarse.values[c] / fine.values[c]) / np.log(ratio):.2f}"
                        for c in columns
                    ]
                )
        lines += _table(["method", "n", *columns], order_rows)
    lines += ["## Checks", ""]
    lines += _table(
        ["check", "backend", "method", "result", "detail"],
        [[c["check"], c["backend"], c["method"], c["status"].upper(), c["detail"]] for c in checks],
    )
    out.write_text("\n".join(lines))


def write_summary(results_dir: Path) -> Path:
    """One line per benchmark and backend of every report under ``results_dir``."""
    rows = []
    for checks_file in sorted(results_dir.rglob("checks.json")):
        workdir = checks_file.parent
        run = json.loads((workdir / "run.json").read_text())
        checks = json.loads(checks_file.read_text())["checks"]
        for backend in run["backends"]:
            mine = [c["status"] for c in checks if c["backend"] == backend]
            table = read_table(workdir / "tables" / f"{backend}.csv")
            wall = sum(row["wall_s"] for row in table.values())
            rows.append(
                [
                    f"[{run['name']}]({workdir.relative_to(results_dir).as_posix()}/report.md)",
                    backend,
                    "smoke" if run["smoke"] else "full",
                    len(run["cases"]),
                    mine.count("pass"),
                    mine.count("fail"),
                    mine.count("skip"),
                    f"{wall:.1f}",
                ]
            )
        for backend, reason in run["skipped"].items():
            rows.append([run["name"], backend, "skipped", 0, 0, 0, 0, reason])
    summary = results_dir / "summary.md"
    summary.write_text(
        "\n".join(
            ["# Verification summary", ""]
            + _table(
                [
                    "benchmark",
                    "backend",
                    "sweep",
                    "cases",
                    "pass",
                    "fail",
                    "skip",
                    "solver wall [s]",
                ],
                rows,
            )
        )
    )
    return summary
