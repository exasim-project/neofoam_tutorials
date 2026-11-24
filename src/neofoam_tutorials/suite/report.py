"""``report.md`` of a benchmark run: the plots, the results table and the checks."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd


def _row(cells: Sequence[object]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return [_row(header), _row(["---"] * len(header)), *(_row(r) for r in rows), ""]


def _cell(value: object) -> str:
    return f"{value:.4e}" if isinstance(value, float) else str(value)


def write_report(
    name: str,
    results: pd.DataFrame,
    checks: Sequence[dict[str, Any]],
    columns: Sequence[str],
    plots: Path,
    out: Path,
) -> None:
    """The plots in ``plots``, the ``columns`` of ``results`` (in its order) and every check."""
    lines = [f"# {name}", "", f"{len(results)} cases; all results: [results.csv](results.csv).", ""]
    for png in sorted(plots.glob("*.png")):
        stem = f"{plots.name}/{png.stem}"
        lines += [f"![{png.stem}]({stem}.png) ([pdf]({stem}.pdf))", ""]
    lines += ["## Results", ""]
    table = results[list(columns)].itertuples(index=False)
    lines += _table(columns, [[_cell(v) for v in row] for row in table])
    lines += ["## Checks", ""]
    lines += _table(
        ["check", "group", "result", "detail"],
        [[c["check"], c["group"], c["status"].upper(), c["detail"]] for c in checks],
    )
    out.write_text("\n".join(lines))
