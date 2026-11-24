"""A verification benchmark as files: ``benchmarks/<category>/<name>/``.

* ``benchmark.yaml`` -- the sweep (``dimensions`` in NeoFOAM's ``params.yaml`` shape,
  ``merge``, the ``smoke`` subset, the ``method`` dimension) and what is done with its
  cases' results (``collect``, ``report``);
* ``case/`` -- the base case, with its ``system/preprocess.yaml``;
* ``plots.py`` -- ``plot(results, references, out)`` (:mod:`.plots` has helpers);
* ``reference/`` -- the stored tables (CSV) the plots read.

:func:`export` writes the benchmark's NeoFOAM sweep (``Sweep.export``: ``sweep.csv``,
``params.yaml``, ``configs/``, ``Snakefile``) to its workflow directory; the
``Snakefile`` includes :data:`BENCHMARK_SMK` (collect -> compare, plots -> report) and
requires ``report.md``.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

#: ``benchmarks/`` of this repository: a benchmark's name is its folder relative to it.
BENCHMARKS = Path(__file__).resolve().parents[3] / "benchmarks"
#: the documentation's committed results, ``<category>/<name>/results.csv`` per benchmark
SNAPSHOTS = BENCHMARKS.parent / "doc" / "_generated"
BENCHMARK_SMK = Path(__file__).with_name("benchmark.smk")
#: NeoFOAM's sweep rules a benchmark runs: the mesh once per mesh variant, then per case
#: setup (configs, mesh copy, the case-level preprocess tools) and solve
RULES = ("all", "setup_mesh", "blockMesh", "setup", "solve")
#: NeoFOAM's mesh dimension: the results are grouped by every other dimension
MESH = "mesh"


def load(folder: Path) -> dict[str, Any]:
    spec: dict[str, Any] = yaml.safe_load((folder / "benchmark.yaml").read_text())
    return spec


def name(folder: Path) -> str:
    """``<category>/<name>``: the folder relative to ``benchmarks/``."""
    try:
        return folder.resolve().relative_to(BENCHMARKS).as_posix()
    except ValueError:
        return folder.name


def dimensions(
    spec: dict[str, Any], smoke: bool = False, methods: Sequence[str] = ()
) -> dict[str, dict[str, Any]]:
    """The swept variants: all, the ``smoke`` subset, or ``methods`` instead of the method's."""
    dims: dict[str, dict[str, Any]] = copy.deepcopy(spec["dimensions"])
    if smoke:
        for dimension, keep in spec["smoke"].items():
            dims[dimension] = {v: dims[dimension][v] for v in keep}
    if methods:
        method = spec["method"]
        dims[method["dimension"]] = {m: {method["entry"]: m} for m in methods}
    return dims


def export(folder: Path, workdir: Path, smoke: bool = False, methods: Sequence[str] = ()) -> Path:
    """Write the benchmark's sweep to ``workdir``; returns its ``Snakefile``."""
    from neofoam.framework.solver.registry import resolve_solver
    from neofoam.tooling.workflow.sweep import Sweep
    from neofoam.tooling.workflow.sweep_runner import config_classes_by_name

    spec = load(folder)
    Sweep(
        dimensions=dimensions(spec, smoke, methods),
        solver_name=spec["solver"],
        base_case=folder.resolve() / "case",
        classes=config_classes_by_name(resolve_solver(spec["solver"])),
        enabled=list(RULES),
        merge=bool(spec.get("merge", False)),
        includes=[BENCHMARK_SMK],
        targets=["report.md"],
    ).export(workdir)
    return workdir / "Snakefile"
