"""The single-phase benchmarks' metrics on synthetic fields and logs, and their checks on
the stored OpenFOAM table."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from neofoam_tutorials.suite.benchmark import load
from neofoam_tutorials.suite.checks import evaluate

SINGLE_PHASE = Path(__file__).resolve().parents[1] / "benchmarks" / "singlePhase"
CAVITY, PITZ_DAILY = SINGLE_PHASE / "cavity", SINGLE_PHASE / "pitzDaily"


def _metrics(folder: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"{folder.name}_metrics", folder / "metrics.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cavity_centrelines_are_exact_for_a_linear_field() -> None:
    n = 8
    x, y = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    centres = np.column_stack([x.ravel(), y.ravel(), np.zeros(n * n)])
    u = np.column_stack([centres[:, 1], centres[:, 0], np.zeros(n * n)])

    ys, u_line, xs, v_line = _metrics(CAVITY).centrelines(centres, u)

    # u = y, v = x at the cell centres; the walls' values (lid 1, else 0) close the lines
    np.testing.assert_allclose(u_line[1:-1], ys[1:-1])
    np.testing.assert_allclose(v_line[1:-1], xs[1:-1])
    assert (u_line[0], u_line[-1], v_line[0], v_line[-1]) == (0, 1, 0, 0)


def test_pitz_daily_reattachment_is_the_last_negative_to_positive_turn() -> None:
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    # a corner vortex (positive near the step), the main recirculation, reattachment
    ux = np.array([0.1, -0.2, -1.0, -0.5, 0.5, 1.0])

    assert _metrics(PITZ_DAILY).reattachment(x, ux) == 3.5


def test_pitz_daily_residuals_and_convergence_from_the_log(tmp_path: Path) -> None:
    lines = []
    for scale in (1.0, 1e-3, 1e-4):
        for field in ("Ux", "Uy", "Uz", "p", "epsilon", "k"):
            residual = 5 * scale if field == "p" else 0.5 * scale
            lines.append(f"smoothSolver:  Solving for {field}, Initial residual = {residual}, x")
        lines.append("ExecutionTime = 0.5 s  ClockTime = 2 s")
    (tmp_path / "log.solver").write_text("\n".join(lines) + "\n")
    metrics = _metrics(PITZ_DAILY)

    table = metrics.residuals(tmp_path / "log.solver")

    assert list(table["Time"]) == [1, 2, 3]
    assert table["p_res"].iloc[1] == 5e-3
    # iteration 2 has U, k, epsilon 5e-4 < 1e-3 and p 5e-3 < 1e-2
    assert metrics.converged_at(table) == 2


def test_stored_openfoam_table_passes_the_pitz_daily_reference_checks() -> None:
    stored = pd.read_csv(PITZ_DAILY / "reference" / "openfoam.csv")
    results = stored.assign(case=stored["mesh"] + "_Serial", executor="Serial")
    checks = [c for c in load(PITZ_DAILY)["checks"] if c.get("file") == "openfoam.csv"]

    out = evaluate(checks, results, PITZ_DAILY / "reference", ["executor"])

    assert len(out) == 2
    assert {c["status"] for c in out} == {"pass"}, out


def test_stored_icofoam_table_passes_the_cavity_reference_and_order_checks() -> None:
    stored = pd.read_csv(CAVITY / "reference" / "icofoam.csv")
    results = stored.assign(
        case=stored["mesh"] + "_Serial", executor="Serial", h=1 / stored["mesh"].str[1:].astype(int)
    )
    checks = [c for c in load(CAVITY)["checks"] if c["type"] in ("reference", "order")]

    out = evaluate(checks, results, CAVITY / "reference", ["executor"])

    assert len(out) == 2
    assert {c["status"] for c in out} == {"pass"}, out
