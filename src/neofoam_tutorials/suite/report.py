"""``report.md`` of a benchmark run: the plots, the results table and the changes against
the documentation's snapshot."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from .changes import FACTOR, FLAGGED


def _row(cells: Sequence[object]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return [_row(header), _row(["---"] * len(header)), *(_row(r) for r in rows), ""]


def _cell(value: object) -> str:
    if value is None:
        return ""
    return f"{value:.4e}" if isinstance(value, float) else str(value)


def write_report(
    name: str,
    results: pd.DataFrame,
    changes: Sequence[dict[str, Any]],
    columns: Sequence[str],
    plots: Path,
    out: Path,
) -> None:
    """The plots in ``plots``, the ``columns`` of ``results`` (in its order) and ``changes``."""
    lines = [f"# {name}", "", f"{len(results)} cases; all results: [results.csv](results.csv).", ""]
    for png in sorted(plots.glob("*.png")):
        stem = f"{plots.name}/{png.stem}"
        lines += [f"![{png.stem}]({stem}.png) ([pdf]({stem}.pdf))", ""]
    lines += ["## Results", ""]
    table = results[list(columns)].itertuples(index=False)
    lines += _table(columns, [[_cell(v) for v in row] for row in table])
    flagged = sum(c["kind"] in FLAGGED for c in changes)
    lines += ["## Changes against the snapshot", ""]
    lines += [
        f"{flagged} flagged (a metric off by more than a factor {FACTOR:g}, a case missing "
        "or NaN); a new case is listed, not flagged.",
        "",
    ]
    if changes:
        lines += _table(
            ["case", "column", "change", "snapshot", "run"],
            [
                [c["case"], c["column"], c["kind"], _cell(c["old"]), _cell(c["new"])]
                for c in changes
            ],
        )
    out.write_text("\n".join(lines))
