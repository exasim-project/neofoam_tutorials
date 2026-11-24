"""The workers of ``benchmark.smk``, run in the benchmark's workflow directory::

    python -m neofoam_tutorials.suite.workflow collect|compare|plots|report \\
        --benchmark FOLDER --out PATH
    python -m neofoam_tutorials.suite.workflow metrics --benchmark FOLDER --out \\
        cases/<case>/postProcessing/metrics.dat

* ``metrics`` -- per solved case, when ``benchmark.yaml`` has ``metrics: {script, prune}``:
  the table of the benchmark's ``script`` (``metrics(case: Path) -> DataFrame``, one row
  per written time, from the case's written fields) as a function-object ``.dat``; with
  ``prune`` the case's time directories but the first and the last are removed after;
* ``collect`` -- per case of ``sweep.csv`` its history: the ``collect.tables`` of the
  solved case (NeoFOAM ``postProcess`` CSVs, ``time`` first, and function-object
  ``.dat`` tables) merged on the time, a later table's column replacing an earlier one
  of the same name, then the ``collect.derive`` script's columns
  (``derive(history, case) -> DataFrame``). ``results.csv``: one row per case, its
  variant per dimension (columns renamed by ``collect.columns``), then the last row of
  its history; beside it, with ``collect.history``, ``histories.csv`` (every row of every
  history) and, with ``collect.profiles``, ``profiles.csv`` (those per-case tables,
  e.g. the metrics' final profiles), both with the case's variant columns;
* ``compare`` -- ``changes.json``: the drastic changes of ``results.csv`` against the
  documentation's snapshot ``doc/_generated/<category>/<name>/results.csv``
  (:mod:`.changes`), rows matched by the dimension columns; it never fails the run;
* ``plots`` -- the benchmark's ``plots.py``: ``plot(results, references, out)``;
* ``report`` -- ``report.md`` (:mod:`.report`).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from .benchmark import MESH, SNAPSHOTS, load, name
from .changes import compare
from .report import write_report

COMMANDS = ("metrics", "collect", "compare", "plots", "report")
#: NeoFOAM's postProcess "no data" sentinel (``neofoam.postprocess.GREAT``): read as NaN
GREAT = 1.0e15
#: beside results.csv: every history row, and the cases' profile tables
HISTORIES, PROFILES = "histories.csv", "profiles.csv"


def read_table(path: Path) -> pd.DataFrame:
    """A function object's whole ``.dat`` (the header's last ``#`` line names the columns)."""
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    header = [line for line in lines if line.startswith("#")][-1].lstrip("#").split()
    rows = [[float(v) for v in line.split()] for line in lines if not line.startswith("#")]
    return pd.DataFrame(rows, columns=header)


def read_post_process(path: Path) -> pd.DataFrame:
    """A NeoFOAM ``postProcess`` CSV, ``time`` renamed ``Time`` and its sentinels NaN."""
    table = pd.read_csv(path, float_precision="round_trip").rename(columns={"time": "Time"})
    values = table.drop(columns="Time")
    table[values.columns] = values.mask(values.abs() >= GREAT)
    return table


def _merge(history: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """``history`` and ``table`` on their times (12 significant digits, as NeoFOAM's CSV
    writes them); a column of ``table`` replaces ``history``'s of the same name."""
    table = table.assign(Time=[float(f"{t:.12g}") for t in table["Time"]]).set_index("Time")
    index = history.index.union(table.index)
    history, table = history.reindex(index), table.reindex(index)
    for column in table.columns:
        history[column] = table[column].combine_first(history.get(column, table[column]))
    return history


def case_history(folder: Path, case: Path) -> pd.DataFrame:
    """The case's ``collect.tables`` merged on the time, then ``collect.derive``'s columns."""
    spec = load(folder)["collect"]
    history = pd.DataFrame(index=pd.Index([], name="Time", dtype=float))
    for table_name in spec["tables"]:
        path = case / table_name
        table = read_post_process(path) if path.suffix == ".csv" else read_table(path)
        history = _merge(history, table)
    history = history.reset_index()
    if "derive" in spec:
        history = _module(folder / spec["derive"], "benchmark_derive").derive(history, case)
    return history


def write_table(table: pd.DataFrame, path: Path) -> None:
    """``table`` as a function-object ``.dat``: a ``# Time ...`` header, then the rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [" ".join(f"{v:.17g}" for v in row) for row in table.itertuples(index=False)]
    path.write_text("\n".join(["# " + " ".join(table.columns), *rows]) + "\n")


def _module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def time_directories(case: Path) -> list[Path]:
    """The case's time directories, in time order."""
    times = []
    for entry in case.iterdir():
        try:
            times.append((float(entry.name), entry))
        except ValueError:
            continue
    return [entry for _, entry in sorted(times)]


def metrics(folder: Path, case: Path, out: Path) -> None:
    """The benchmark's metrics table of ``case``, then (``prune``) its inner time dirs removed."""
    spec = load(folder)["metrics"]
    table = _module(folder / spec["script"], "benchmark_metrics").metrics(case)
    write_table(table, out)
    if spec.get("prune", False):
        for time in time_directories(case)[1:-1]:
            shutil.rmtree(time)


def collect(folder: Path, workdir: Path, out: Path) -> None:
    """``results.csv`` (``out``), and ``histories.csv`` and ``profiles.csv`` beside it.

    The rows by group, then in the mesh variants' order of ``benchmark.yaml``.
    """
    spec = load(folder)
    renamed = spec["collect"].get("columns", {})
    rows, histories, profiles = [], [], []
    for case in pd.read_csv(workdir / "sweep.csv", dtype=str).to_dict("records"):
        variants = {renamed.get(k, k): v for k, v in case.items()}
        case_dir = workdir / "cases" / case["case"]
        history = case_history(folder, case_dir)
        rows.append(variants | history.iloc[-1].to_dict())
        histories.append(history.assign(**variants))
        for profile_name in spec["collect"].get("profiles", []):
            profile = pd.read_csv(case_dir / profile_name, float_precision="round_trip")
            profiles.append(profile.assign(**variants))
    meshes = list(spec["dimensions"][MESH])
    results = pd.DataFrame(rows)
    results["_mesh"] = results[mesh_column(folder)].map(meshes.index)
    results = results.sort_values([*groups(folder), "_mesh"]).drop(columns="_mesh")
    results.to_csv(out, index=False, float_format="%.17g")
    order = {name: i for i, name in enumerate(results["case"])}

    def by_results(tables: list[pd.DataFrame]) -> pd.DataFrame:
        table = pd.concat(tables, ignore_index=True)
        variants = list(results.columns[: len(case)])
        table = table[[*variants, *(c for c in table.columns if c not in variants)]]
        return table.sort_values("case", key=lambda c: c.map(order), kind="stable")

    if spec["collect"].get("history", False):
        by_results(histories).to_csv(out.with_name(HISTORIES), index=False, float_format="%.17g")
    if profiles:
        by_results(profiles).to_csv(out.with_name(PROFILES), index=False, float_format="%.17g")


def mesh_column(folder: Path) -> str:
    return str(load(folder)["collect"].get("columns", {}).get(MESH, MESH))


def groups(folder: Path) -> list[str]:
    """The results' columns of the dimensions but the mesh."""
    spec = load(folder)
    renamed = spec["collect"].get("columns", {})
    return [renamed.get(d, d) for d in sorted(spec["dimensions"]) if d != MESH]


def changes(folder: Path, results: pd.DataFrame) -> list[dict[str, Any]]:
    """:func:`.changes.compare` of ``results`` against the benchmark's snapshot, if any."""
    snapshot = SNAPSHOTS / name(folder) / "results.csv"
    old = pd.read_csv(snapshot) if snapshot.exists() else results.iloc[0:0]
    return compare(results, old, [*groups(folder), mesh_column(folder)])


def references(folder: Path) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_csv(p) for p in sorted((folder / "reference").glob("*.csv"))}


def plot(folder: Path, results: pd.DataFrame, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _module(folder / "plots.py", "benchmark_plots").plot(results, references(folder), out)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m neofoam_tutorials.suite.workflow")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    folder, workdir = args.benchmark, Path.cwd()
    if args.command == "metrics":
        # out is cases/<case>/postProcessing/metrics.dat
        metrics(folder, args.out.parents[1], args.out)
        return
    if args.command == "collect":
        collect(folder, workdir, args.out)
        return
    results = pd.read_csv(workdir / "results.csv")
    if args.command == "compare":
        args.out.write_text(json.dumps({"changes": changes(folder, results)}, indent=2) + "\n")
    elif args.command == "plots":
        plot(folder, results, args.out)
    else:
        found = json.loads((workdir / "changes.json").read_text())["changes"]
        columns = [*groups(folder), mesh_column(folder), *load(folder).get("report", [])]
        write_report(name(folder), results, found, columns, workdir / "plots", args.out)


if __name__ == "__main__":
    main()
