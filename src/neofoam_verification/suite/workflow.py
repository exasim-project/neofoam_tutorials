"""The workers of ``benchmark.smk``, run in the benchmark's workflow directory::

    python -m neofoam_verification.suite.workflow collect|verify|plots|report \\
        --benchmark FOLDER --out PATH

* ``collect`` -- ``results.csv``: one row per case of ``sweep.csv``, its variant per
  dimension (columns renamed by ``collect.columns``), then the last row of each
  ``collect.tables`` function-object table of the solved case;
* ``verify`` -- ``checks.json``: the ``checks`` of ``benchmark.yaml`` (:mod:`.checks`);
* ``plots`` -- the benchmark's ``plots.py``: ``plot(results, references, out)``;
* ``report`` -- ``report.md`` (:mod:`.report`).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from .benchmark import MESH, load, name
from .checks import evaluate
from .report import write_report

COMMANDS = ("collect", "verify", "plots", "report")


def read_dat(path: Path) -> dict[str, float]:
    """The last row of a function object's ``.dat`` by column, ``Time`` included."""
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    header = [line for line in lines if line.startswith("#")][-1].lstrip("#").split()
    row = [line for line in lines if not line.startswith("#")][-1].split()
    return dict(zip(header, (float(v) for v in row), strict=True))


def collect(folder: Path, workdir: Path) -> pd.DataFrame:
    """The rows by group, then in the mesh variants' order of ``benchmark.yaml``."""
    spec = load(folder)
    renamed = spec["collect"].get("columns", {})
    rows = []
    for case in pd.read_csv(workdir / "sweep.csv", dtype=str).to_dict("records"):
        row: dict[str, object] = {renamed.get(k, k): v for k, v in case.items()}
        for table in spec["collect"]["tables"]:
            row |= read_dat(workdir / "cases" / case["case"] / table)
        rows.append(row)
    meshes = list(spec["dimensions"][MESH])
    results = pd.DataFrame(rows)
    results["_mesh"] = results[mesh_column(folder)].map(meshes.index)
    return results.sort_values([*groups(folder), "_mesh"]).drop(columns="_mesh")


def mesh_column(folder: Path) -> str:
    return str(load(folder)["collect"].get("columns", {}).get(MESH, MESH))


def groups(folder: Path) -> list[str]:
    """The results' columns of the dimensions but the mesh: one check result each."""
    spec = load(folder)
    renamed = spec["collect"].get("columns", {})
    return [renamed.get(d, d) for d in sorted(spec["dimensions"]) if d != MESH]


def references(folder: Path) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_csv(p) for p in sorted((folder / "reference").glob("*.csv"))}


def plot(folder: Path, results: pd.DataFrame, out: Path) -> None:
    spec = importlib.util.spec_from_file_location("benchmark_plots", folder / "plots.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {folder / 'plots.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out.mkdir(parents=True, exist_ok=True)
    module.plot(results, references(folder), out)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m neofoam_verification.suite.workflow")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    folder, workdir = args.benchmark, Path.cwd()
    if args.command == "collect":
        collect(folder, workdir).to_csv(args.out, index=False, float_format="%.17g")
        return
    results = pd.read_csv(workdir / "results.csv")
    if args.command == "verify":
        checks = evaluate(load(folder)["checks"], results, folder / "reference", groups(folder))
        args.out.write_text(json.dumps({"checks": checks}, indent=2) + "\n")
    elif args.command == "plots":
        plot(folder, results, args.out)
    else:
        checks = json.loads((workdir / "checks.json").read_text())["checks"]
        columns = [*groups(folder), mesh_column(folder), *load(folder).get("report", [])]
        write_report(name(folder), results, checks, columns, workdir / "plots", args.out)


if __name__ == "__main__":
    main()
