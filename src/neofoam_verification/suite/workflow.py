"""A benchmark as a Snakemake workflow: the export and the workers its rules call.

:func:`export` writes the workflow directory ``results/<category>/<name>/``:

* ``sweep.csv`` + ``params.yaml`` -- the sweep in NeoFOAM's paramspace format
  (:mod:`neofoam.tooling.workflow.paramspace`): one row per case, one dimension
  ``simulation_parameters`` whose variants are the ``system/simulationParameters``
  entries; ``configs/<case>/simulation_parameters.json`` materialised from them
  (rewritten only when changed, so Snakemake reruns exactly the changed cases);
* ``run.json`` -- the benchmark, the cases' method and resolution, the backends that
  run and the ones skipped (with the reason);
* ``Snakefile`` -- per backend and case ``generate`` (template copy, ``0.orig`` -> ``0``,
  simulationParameters) -> one rule per preparation step (``blockMesh``,
  ``setAlphaField``, ...) -> ``solve``; per backend ``table`` (``tables/<backend>.csv``);
  ``results`` (``results.csv``, long format); ``plots`` (``plots/<name>.png|pdf``, the
benchmark's ``plots``); ``verify`` (``checks.json``); ``report`` (``report.md``).

The rules call ``python -m neofoam_verification.suite.workflow <command>``.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml
from foamlib import FoamFile

from . import backends as backends_module
from .benchmark import Benchmark, Case, load
from .checks import Keyed, Result, read_table, write_table
from .plots import FORMATS, draw_all, plot_name
from .report import write_report

DIMENSION = "simulation_parameters"
WORKER = "python -m neofoam_verification.suite.workflow"


def write_if_changed(path: Path, text: str) -> None:
    """As paramspace's: an unchanged file keeps its mtime, so its jobs do not rerun."""
    if path.is_file() and path.read_text() == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def export(
    benchmark: Benchmark,
    workdir: Path,
    cases: Sequence[Case],
    backends: Sequence[str],
    skipped: dict[str, str],
    smoke: bool,
) -> Path:
    """Write the workflow of ``cases`` on ``backends`` to ``workdir``; returns the Snakefile."""
    workdir.mkdir(parents=True, exist_ok=True)
    with (workdir / "sweep.csv").open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["case", DIMENSION])
        writer.writerows([case.name, case.name] for case in cases)
    params = {DIMENSION: {case.name: case.parameters for case in cases}}
    write_if_changed(workdir / "params.yaml", yaml.safe_dump(params, sort_keys=True))
    for case in cases:
        text = json.dumps({DIMENSION: case.parameters}, sort_keys=True, indent=2) + "\n"
        write_if_changed(workdir / "configs" / case.name / f"{DIMENSION}.json", text)
    run = {
        "benchmark": str(benchmark.folder / "benchmark.py"),
        "name": benchmark.name,
        "solver": benchmark.solver,
        "smoke": smoke,
        "cases": [asdict(case) | {"name": case.name} for case in cases],
        "backends": list(backends),
        "skipped": skipped,
    }
    write_if_changed(workdir / "run.json", json.dumps(run, indent=2) + "\n")
    snakefile = workdir / "Snakefile"
    write_if_changed(snakefile, snakefile_text(benchmark, [c.name for c in cases], backends))
    return snakefile


def snakefile_text(benchmark: Benchmark, case_names: Sequence[str], backends: Sequence[str]) -> str:
    benchmark_py = benchmark.folder / "benchmark.py"
    steps = {step.name: [b for b in backends if step.applies_to(b)] for step in benchmark.prepare}
    plot_files = [f"plots/{plot_name(p)}.{fmt}" for p in benchmark.plots for fmt in FORMATS]
    verify_inputs = [str(benchmark_py), *map(str, sorted(benchmark.reference.glob("*")))]
    lines = [
        f"# Generated from {benchmark_py} by neofoam_verification.suite.workflow.export.",
        f"BENCHMARK = {str(benchmark_py)!r}",
        f"CASES = {list(case_names)!r}",
        f"BACKENDS = {list(backends)!r}",
        f"STEPS = {steps!r}",
        f"WORKER = {WORKER!r}",
        "# the checks read these: a changed benchmark.py or reference table reruns verify",
        f"VERIFY_INPUTS = {verify_inputs!r}",
        f"PLOTS = {plot_files!r}",
        "",
        "wildcard_constraints:",
        '    case="[^/]+",',
        f'    backend="{"|".join(backends) or "none"}",',
        "",
        "",
        "def before(step, wc):",
        '    """The stamp of the last step the backend runs before ``step`` (None: solve)."""',
        "    names = list(STEPS)",
        "    names = names[: names.index(step)] if step else names",
        '    done = [s for s in names if wc.backend in STEPS[s]] or ["generate"]',
        '    return f"cases/{wc.backend}/{wc.case}/.{done[-1]}.done"',
        "",
        "",
        "rule all:",
        '    input: "report.md"',
        "",
        "rule generate:",
        f'    input: "configs/{{case}}/{DIMENSION}.json"',
        '    output: "cases/{backend}/{case}/.generate.done"',
        "    shell: WORKER + \" generate --benchmark '{BENCHMARK}' --config '{input}'"
        " --case 'cases/{wildcards.backend}/{wildcards.case}' --stamp '{output}'\"",
        "",
    ]
    for name, step_backends in steps.items():
        lines += [
            f"rule {name}:",
            f"    input: lambda wc: before({name!r}, wc)",
            f'    output: "cases/{{backend}}/{{case}}/.{name}.done"',
            f'    wildcard_constraints: backend="{"|".join(step_backends) or "none"}"',
            f"    shell: WORKER + \" step --benchmark '{{BENCHMARK}}' --step {name}"
            " --backend {wildcards.backend} --case 'cases/{wildcards.backend}/{wildcards.case}'"
            " --stamp '{output}'\"",
            "",
        ]
    lines += [
        "rule solve:",
        "    input: lambda wc: before(None, wc)",
        '    output: "cases/{backend}/{case}/.solve.json"',
        "    shell: WORKER + \" solve --benchmark '{BENCHMARK}' --backend {wildcards.backend}"
        " --case 'cases/{wildcards.backend}/{wildcards.case}' --stamp '{output}'\"",
        "",
        "rule table:",
        '    input: expand("cases/{{backend}}/{case}/.solve.json", case=CASES)',
        '    output: "tables/{backend}.csv"',
        "    shell: WORKER + \" table --benchmark '{BENCHMARK}' --backend {wildcards.backend}"
        " --out '{output}'\"",
        "",
        "rule results:",
        '    input: expand("tables/{backend}.csv", backend=BACKENDS), "run.json"',
        '    output: "results.csv"',
        "    shell: WORKER + \" results --benchmark '{BENCHMARK}' --out '{output}'\"",
        "",
        "rule plots:",
        '    input: "results.csv"',
        "    output: PLOTS",
        "    shell: WORKER + \" plots --benchmark '{BENCHMARK}' --out plots\"",
        "",
        "rule verify:",
        '    input: expand("tables/{backend}.csv", backend=BACKENDS), "run.json", VERIFY_INPUTS',
        '    output: "checks.json"',
        "    shell: WORKER + \" verify --benchmark '{BENCHMARK}' --out '{output}'\"",
        "",
        "rule report:",
        '    input: "checks.json", "results.csv", PLOTS',
        '    output: "report.md"',
        "    shell: WORKER + \" report --benchmark '{BENCHMARK}' --out '{output}'\"",
        "",
    ]
    return "\n".join(lines)


# -- the workers (cwd: the workflow directory) ----------------------------------------


def _stamp(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def generate(benchmark: Benchmark, config: Path, case: Path) -> None:
    """A fresh copy of the template with ``0.orig`` -> ``0`` and the case's parameters."""
    if case.exists():
        shutil.rmtree(case)
    shutil.copytree(benchmark.case, case)
    if (case / "0.orig").is_dir():
        shutil.copytree(case / "0.orig", case / "0")
    parameters = FoamFile(case / "system" / "simulationParameters")
    for key, value in json.loads(config.read_text())[DIMENSION].items():
        parameters[key] = value


def step(benchmark: Benchmark, name: str, backend: str, case: Path) -> None:
    (prepare,) = [s for s in benchmark.prepare if s.name == name]
    for i, command in enumerate(prepare.commands_for(case.resolve())):
        backends_module.run(backends_module.BACKENDS[backend], case, command, f"log.{name}.{i}")


def solve(benchmark: Benchmark, backend: str, case: Path) -> dict[str, Any]:
    chosen = backends_module.BACKENDS[backend]
    command = chosen.solver_command(benchmark.solver)
    start = time.perf_counter()
    backends_module.run(chosen, case, command, f"log.{benchmark.solver}")
    return {"backend": backend, "command": command, "wall_s": time.perf_counter() - start}


def results(workdir: Path) -> list[Result]:
    run = json.loads((workdir / "run.json").read_text())
    out = []
    for backend in run["backends"]:
        for (method, n), values in read_table(workdir / "tables" / f"{backend}.csv").items():
            out.append(Result(backend, method, n, values))
    return out


def table(benchmark: Benchmark, backend: str, workdir: Path) -> Keyed:
    run = json.loads((workdir / "run.json").read_text())
    rows: Keyed = {}
    for case in run["cases"]:
        directory = workdir / "cases" / backend / case["name"]
        row = benchmark.table.read(directory)
        row["wall_s"] = json.loads((directory / ".solve.json").read_text())["wall_s"]
        rows[case["method"], case["resolution"]] = row
    return rows


def results_columns(benchmark: Benchmark) -> tuple[str, ...]:
    return benchmark.results_columns or (*benchmark.table.columns, "wall_s")


def write_results(benchmark: Benchmark, workdir: Path, out: Path) -> None:
    """``results.csv``: one row per backend, method and resolution (long format)."""
    columns = results_columns(benchmark)
    with out.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["backend", "executor", "method", "n", *columns])
        for r in sorted(results(workdir), key=lambda r: (r.backend, r.method, r.resolution)):
            executor = backends_module.BACKENDS[r.backend].executor
            values = (f"{r.values[c]:.17g}" for c in columns)
            writer.writerow([r.backend, executor, r.method, r.resolution, *values])


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog=WORKER)
    parser.add_argument(
        "command",
        choices=("generate", "step", "solve", "table", "results", "plots", "verify", "report"),
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--step")
    parser.add_argument("--backend")
    parser.add_argument("--stamp", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    benchmark = load(args.benchmark)
    workdir = Path.cwd()
    if args.command == "generate":
        generate(benchmark, args.config, args.case)
        _stamp(args.stamp, {"config": str(args.config)})
    elif args.command == "step":
        step(benchmark, args.step, args.backend, args.case)
        _stamp(args.stamp, {"step": args.step, "backend": args.backend})
    elif args.command == "solve":
        _stamp(args.stamp, solve(benchmark, args.backend, args.case))
    elif args.command == "table":
        rows = table(benchmark, args.backend, workdir)
        write_table(args.out, rows, [*benchmark.table.columns, "wall_s"])
    elif args.command == "results":
        write_results(benchmark, workdir, args.out)
    elif args.command == "plots":
        reference = benchmark.reference_backend
        draw_all(benchmark.plots, workdir / "results.csv", args.out, reference)
    elif args.command == "verify":
        checks = [r for c in benchmark.checks for r in c.evaluate(benchmark, results(workdir))]
        _stamp(args.out, {"checks": [asdict(c) for c in checks]})
    else:
        write_report(benchmark, workdir, results(workdir), args.out)


if __name__ == "__main__":
    main()
