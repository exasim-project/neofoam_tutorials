"""The readable tables of each benchmark page: ``doc/_generated/<category>/<name>/*.rst``.

``conf.py`` calls :func:`render_all` (after ``sync_results.render_all``). Per benchmark:

* ``params.rst`` -- "Changed parameters" from ``benchmark.yaml``: one row per dimension
  (``Parameter | Meaning | Values | Smoke run``) and the case count. :data:`DIMENSIONS`
  says how to read a dimension's payloads, :data:`NOTES` adds a benchmark's remark;
* ``key_results.rst`` -- the :data:`KEY` columns of ``results.csv`` under the
  :data:`HEADERS` names, for the base executor, with the wall time per executor and the
  executors' largest relative difference.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks"
GENERATED = ROOT / "doc" / "_generated"

Payloads = dict[str, Any]


def _cells(payload: Payloads) -> list[int]:
    """The block's cell counts, without the one-cell (empty) direction."""
    cells = payload["block_mesh_dict_config"]["blocks"][0]["cells"]
    return [c for c in cells if c != 1] or [1]


def _mesh(payload: Payloads) -> str:
    cells = _cells(payload)
    return str(cells[0]) if len(set(cells)) == 1 else " × ".join(map(str, cells))


def _mesh_meaning(variants: dict[str, Payloads]) -> str:
    square = all(len(set(_cells(p))) == 1 for p in variants.values())
    dim = len(_cells(next(iter(variants.values()))))
    if square:
        return f"cells per side n ({' × '.join(['n'] * dim)}; ``blockMeshDict`` blocks)"
    return "cells per direction (``blockMeshDict`` blocks)"


def _entry(key: str) -> Callable[[Payloads], str]:
    """A payload ``{key: value}``: show the value."""
    return lambda payload: str(payload[key])


_EXECUTORS = {"Serial": "Serial", "CPU": "CPU (OpenMP)", "GPU": "GPU (CUDA)"}

#: dimension -> (label, meaning, payload -> shown value); the meaning may be a function of
#: the dimension's variants
DIMENSIONS: dict[str, tuple[str, str | Callable[[dict[str, Payloads]], str], Any]] = {
    "mesh": ("Mesh", _mesh_meaning, _mesh),
    "neo_n_control_config": (
        "Executor",
        "NeoN backend (``controlDict`` ``executor``)",
        lambda p: _EXECUTORS.get(p["executor"], p["executor"]),
    ),
    "reconstruction_scheme_config": (
        "Method",
        "interface reconstruction (``fvSolution`` ``reconstructionScheme``)",
        _entry("reconstructionScheme"),
    ),
    "advection_scheme_config": (
        "Method",
        "interface advection (``fvSolution`` ``advectionScheme``)",
        _entry("advectionScheme"),
    ),
}

#: ``controlDict`` entries a ``control_dict_config`` variant may set: key -> (label, meaning)
CONTROL_DICT = {
    "maxAlphaCo": ("CFL (``maxAlphaCo``)", "interface Courant number; sets the fixed dt"),
    "deltaT": ("Time step (``deltaT``)", "fixed time step [s]"),
    "endTime": ("End time (``endTime``)", "simulated time [s]"),
}

#: benchmark -> dimension -> a remark appended to the meaning
NOTES: dict[str, dict[str, str]] = {
    "surfaceTension/staticDrop": {"mesh": "R/dx = n/4"},
    "advection/discUniFlow": {"mesh": "n80 … n320 commented out"},
    "singlePhase/pitzDaily": {
        "mesh": "shown: the first of five blocks; ``tutorial`` is OpenFOAM's mesh (12 225 "
        "cells), ``coarse`` halves every block (3 122 cells)"
    },
}


def _row(
    name: str, dimension: str, variants: dict[str, Payloads], smoke: list[str] | None
) -> list[str]:
    if dimension == "control_dict_config":
        keys = {k for p in variants.values() for k in p}
        key = keys.pop() if len(keys) == 1 else ""
        label, meaning = CONTROL_DICT.get(key, (f"``{dimension}``", ""))
        show: Callable[[Payloads], str] = (lambda p: str(p[key])) if key else str
    elif dimension in DIMENSIONS:
        label, meaning_of, show = DIMENSIONS[dimension]
        meaning = meaning_of(variants) if callable(meaning_of) else meaning_of
    else:
        label, meaning, show = f"``{dimension}``", "", None
    note = NOTES.get(name, {}).get(dimension)
    if note:
        meaning = f"{meaning}; {note}" if meaning else note

    def values(keep: list[str]) -> str:
        return ", ".join(show(variants[v]) if show else f"``{v}``" for v in keep)

    smoke_values = "all" if smoke is None or len(smoke) == len(variants) else values(smoke)
    return [label, meaning, values(list(variants)), smoke_values]


def _list_table(header: list[str], rows: list[list[str]], widths: str) -> list[str]:
    lines = [".. list-table::", "   :header-rows: 1", f"   :widths: {widths}", ""]
    for row in [header, *rows]:
        lines += [f"   * - {row[0]}", *(f"     - {cell}" for cell in row[1:])]
    return [*lines, ""]


def render_params(name: str) -> None:
    folder = BENCHMARKS / name
    spec = yaml.safe_load((folder / "benchmark.yaml").read_text())
    dims: dict[str, dict[str, Payloads]] = spec["dimensions"]
    smoke: dict[str, list[str]] = spec.get("smoke", {})
    rows = [_row(name, d, v, smoke.get(d)) for d, v in dims.items()]
    full = math.prod(len(v) for v in dims.values())
    reduced = math.prod(len(smoke.get(d, v)) for d, v in dims.items())
    counts = " × ".join(str(len(v)) for v in dims.values())
    lines = _list_table(["Parameter", "Meaning", "Values", "Smoke run"], rows, "16 40 30 14")
    lines += [
        f"**{full} cases** ({counts}); the smoke run (``--smoke``) has {reduced}. "
        f"The raw payloads are in ``benchmarks/{name}/benchmark.yaml``.",
        "",
    ]
    out = GENERATED / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.rst").write_text("\n".join(lines))


#: benchmark -> the results.csv columns of its key-results table
KEY = {
    "reconstruction/circle": ["LNormalInf", "LNormal1", "LCentreInf", "LCentre1"],
    "advection/discUniFlow": ["Eshape", "Emass", "Ebound", "steps"],
    "advection/discUniFlowTestsuite": ["Eshape", "Emass", "Ebound", "steps"],
    "surfaceTension/staticDrop": ["dp", "sigma_R", "dp_err", "maxU_max", "Ca_max"],
    "acceleration/tiltedBox": ["maxU_10ms", "maxU_max", "p_err_max", "p_err_mean"],
    "singlePhase/cavity": ["u_L2", "u_Linf", "v_L2", "v_Linf", "dU", "steps"],
    "singlePhase/pitzDaily": ["nCells", "x_r_h", "Umin_xh1", "Umin_xh3", "Umin_xh5"],
}

#: results.csv column -> readable header
HEADERS = {
    "mesh": "Mesh",
    "method": "Method",
    "CFL": "CFL",
    "LNormalInf": "normal L∞",
    "LNormal1": "normal L1",
    "LCentreInf": "centre L∞",
    "LCentre1": "centre L1",
    "Eshape": "E1 (shape)",
    "Emass": "mass error",
    "Ebound": "bound error",
    "steps": "steps",
    "dp": "Δp [Pa]",
    "sigma_R": "σ/R [Pa]",
    "dp_err": "\\|Δp R/σ − 1\\|",
    "maxU_max": "max\\|U\\| over t [m/s]",
    "Ca_max": "Ca max",
    "maxU_10ms": "max\\|U\\| at 0.01 s [m/s]",
    "p_err_max": "p error max",
    "p_err_mean": "p error mean",
    "u_L2": "u error L2 [m/s]",
    "u_Linf": "u error L∞ [m/s]",
    "v_L2": "v error L2 [m/s]",
    "v_Linf": "v error L∞ [m/s]",
    "dU": "\\|ΔU\\| last 2 s [m/s]",
    "nCells": "cells",
    "x_r_h": "x_r / h",
    "Umin_xh1": "min Ux/U, x/h = 1",
    "Umin_xh3": "x/h = 3",
    "Umin_xh5": "x/h = 5",
}

EXECUTOR, BASE, WALL = "executor", "Serial", "wall_s"
#: the executor agreement leaves out round-off-level values below this
FLOOR = 1e-10


def _num(value: object) -> str:
    if isinstance(value, float):
        return "" if math.isnan(value) else f"{value:.4g}"
    return str(value)


def render_key_results(name: str) -> None:
    out = GENERATED / name
    results = pd.read_csv(out / "results.csv")
    key = KEY[name]
    groups = [c for c in results.columns[1 : results.columns.get_loc("Time")] if c != EXECUTOR]
    shown = [c for c in groups if results[c].nunique() > 1]
    executors = []
    if EXECUTOR in results:
        executors = [BASE, *(e for e in dict.fromkeys(results[EXECUTOR]) if e != BASE)]
    base = results[results[EXECUTOR] == BASE] if executors else results
    order = {v: i for c in groups for i, v in enumerate(dict.fromkeys(results[c]))}
    base = base.sort_values(groups, key=lambda col: col.map(order))
    header = [HEADERS.get(c, c) for c in [*shown, *key]]
    if executors and WALL in results:
        header.append(f"wall [s] {' / '.join(executors)}")
    rows = []
    for _, row in base.iterrows():
        cells = [_num(row[c]) for c in [*shown, *key]]
        if executors and WALL in results:
            same = (results[groups] == row[groups]).all(axis=1)
            wall = results[same].set_index(EXECUTOR)[WALL]
            cells.append(" / ".join(f"{wall[e]:.2g}" for e in executors))
        rows.append(cells)
    lines = _list_table(header, rows, "auto")
    if len(executors) > 1:
        merged = results.merge(base[[*groups, *key]], on=groups, suffixes=("", "_base"))
        diff = 0.0
        for c in key:
            ref = merged[f"{c}_base"].abs()
            rel = (merged[c] - merged[f"{c}_base"]).abs()[ref > FLOOR] / ref[ref > FLOOR]
            diff = max(diff, float(rel.max()) if len(rel) else 0.0)
        others = " and ".join(e for e in executors if e != BASE)
        agree = (
            "are bitwise identical to it in these columns"
            if diff == 0
            else f"agree with it to {diff:.1g} (relative, in these columns; round-off "
            f"values below {FLOOR:g} left out)"
        )
        lines += [f"Rows: the {BASE} executor. {others} {agree}.", ""]
    lines += [
        f"All {len(results)} cases and columns: "
        f":download:`results.csv </_generated/{name}/results.csv>`, changes against the "
        f"previous snapshot: :download:`changes.json </_generated/{name}/changes.json>`.",
        "",
    ]
    (out / "key_results.rst").write_text("\n".join(lines))


def render_all() -> None:
    for path in sorted(BENCHMARKS.rglob("benchmark.yaml")):
        name = path.parent.relative_to(BENCHMARKS).as_posix()
        render_params(name)
        if name in KEY and (GENERATED / name / "results.csv").exists():
            render_key_results(name)


if __name__ == "__main__":
    render_all()
