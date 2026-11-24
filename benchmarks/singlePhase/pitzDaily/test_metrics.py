"""The pitzDaily benchmark's metrics (``metrics.py``) on synthetic profiles and logs."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

PITZ_DAILY = Path(__file__).resolve().parent


def _metrics(folder: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"{folder.name}_metrics", folder / "metrics.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
