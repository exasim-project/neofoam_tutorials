"""``pixi run benchmark FOLDER``: run every ``benchmark.py`` under FOLDER as a Snakemake workflow.

Per benchmark the workflow is exported to ``results/<category>/<name>/``
(:mod:`.suite.workflow`) and run by Snakemake there, then ``results/summary.md`` is
rewritten. Options::

    --method NAME   run NAME instead of the sweep's methods (repeatable), e.g. a newly
                    registered reconstruction scheme
    --smoke         the sweep's smoke resolutions only
    --backend NAME  run only these backends (repeatable; default: the benchmark's)
    -j N            Snakemake cores (at most 4)
    --store-reference BACKEND
                    after a full run, merge BACKEND's table into the benchmark's
                    ``reference/<BACKEND>.csv`` (the verified table AgainstBackend reads)
    --rerun RULE    rerun RULE's jobs and what depends on them (``solve`` after changing
                    the method's code, which the workflow does not see; repeatable)
    --in-process    run without Snakemake (not implemented yet)

A backend that cannot run here (:meth:`Backend.unavailable`) is skipped with its reason
in the report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from .suite.backends import BACKENDS
from .suite.benchmark import Benchmark, cases, discover, load
from .suite.checks import read_table, write_table
from .suite.report import write_summary
from .suite.workflow import export

RESULTS = Path(__file__).resolve().parents[2] / "results"
MAX_CORES = 4


def run_benchmark(
    benchmark: Benchmark,
    results_dir: Path,
    methods: Sequence[str] = (),
    smoke: bool = False,
    backends: Sequence[str] = (),
    cores: int = 1,
    rerun: Sequence[str] = (),
) -> int:
    """Export and run one benchmark's workflow; Snakemake's return code."""
    chosen = [b for b in benchmark.backends if not backends or b in backends]
    skipped = {}
    for name in chosen:
        reason = BACKENDS[name].unavailable(benchmark.solver)
        if reason is not None:
            skipped[name] = reason
    running = [b for b in chosen if b not in skipped]
    workdir = results_dir / benchmark.name
    snakefile = export(
        benchmark, workdir, cases(benchmark, methods, smoke), running, skipped, smoke
    )
    command = ["snakemake", "-s", str(snakefile), "-d", str(workdir), "-c", str(cores)]
    print(f"{benchmark.name}: {' '.join(command)}", flush=True)
    force = ["--forcerun", *rerun] if rerun else []
    return subprocess.run(command + ["--rerun-incomplete", "--quiet", "rules", *force]).returncode


def store_reference(benchmark: Benchmark, results_dir: Path, backend: str) -> Path:
    """Merge the run's ``tables/<backend>.csv`` into ``reference/<backend>.csv`` (no timings)."""
    path = benchmark.reference / f"{backend}.csv"
    stored = read_table(path) if path.is_file() else {}
    stored |= read_table(results_dir / benchmark.name / "tables" / f"{backend}.csv")
    write_table(path, stored, benchmark.table.stored_columns)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m neofoam_verification.run")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--method", action="append", default=[])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--backend", action="append", default=[])
    parser.add_argument("-j", type=int, default=MAX_CORES)
    parser.add_argument("--store-reference", metavar="BACKEND")
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--rerun", action="append", default=[], metavar="RULE")
    parser.add_argument("--in-process", action="store_true")
    args = parser.parse_args(argv)
    if args.in_process:
        raise NotImplementedError("the in-process runner is deferred; the Snakemake workflow runs")
    if args.store_reference and (args.smoke or args.method):
        parser.error("--store-reference needs a full sweep of the benchmark's methods")
    unknown = set(args.backend) - set(BACKENDS)
    if unknown:
        parser.error(f"unknown backend(s) {sorted(unknown)}; known: {sorted(BACKENDS)}")
    paths = discover(args.folder)
    if not paths:
        parser.error(f"no benchmark.py under {args.folder}")
    failed = 0
    for path in paths:
        benchmark = load(path)
        code = run_benchmark(
            benchmark,
            args.results,
            args.method,
            args.smoke,
            args.backend,
            min(args.j, MAX_CORES),
            args.rerun,
        )
        checks_file = args.results / benchmark.name / "checks.json"
        checks = json.loads(checks_file.read_text())["checks"] if code == 0 else []
        failing = [c for c in checks if c["status"] == "fail"]
        failed += code != 0 or bool(failing)
        if code == 0 and args.store_reference:
            if any(c["backend"] == args.store_reference for c in failing):
                print(f"not stored: {args.store_reference} fails a check")
            else:
                print(f"stored {store_reference(benchmark, args.results, args.store_reference)}")
    print(f"summary: {write_summary(args.results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
