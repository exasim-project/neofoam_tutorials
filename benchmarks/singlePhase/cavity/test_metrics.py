"""The cavity benchmark's metrics (``metrics.py``) on a synthetic field."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

CAVITY = Path(__file__).resolve().parent


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
