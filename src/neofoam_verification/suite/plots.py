"""The plots of a benchmark run, drawn from its ``results.csv``.

A benchmark lists them (``plots=(ErrorPlot(NORMS), TimingPlot("k1", ...), ...)``); the
workflow's ``plots`` rule draws each to ``plots/<name>.png`` and ``.pdf``. The x axis is
the resolution ``n`` (cells per side), both axes logarithmic, one line per backend (and
method, when a run has several); the ``reference`` backend is dashed.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

#: One row of ``results.csv``: backend, executor, method, n and the result columns.
ResultRow = dict[str, str]
FORMATS = ("png", "pdf")
MARKERS = ("o", "s", "^", "v", "D", "x")


class Plot(Protocol):
    @property
    def name(self) -> str: ...

    def draw(self, rows: Sequence[ResultRow], reference: str) -> Any:
        """The figure of the rows (a matplotlib Figure)."""
        ...


def read_results(path: Path) -> list[ResultRow]:
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def _lines(rows: Sequence[ResultRow]) -> dict[str, list[ResultRow]]:
    """The rows per line label (``backend``, or ``backend method`` for several methods)."""
    several = len({r["method"] for r in rows}) > 1
    lines: dict[str, list[ResultRow]] = {}
    for row in sorted(rows, key=lambda r: (r["backend"], r["method"], int(r["n"]))):
        label = f"{row['backend']} {row['method']}" if several else row["backend"]
        lines.setdefault(label, []).append(row)
    return lines


def _plot_lines(ax: Any, rows: Sequence[ResultRow], column: str, reference: str) -> None:
    for i, (label, line) in enumerate(_lines(rows).items()):
        dashed = line[0]["backend"] == reference
        # log axes: a zero (e.g. a CPU time below the clock's resolution) is left out
        shown = [r for r in line if float(r[column]) > 0]
        ax.loglog(
            [int(r["n"]) for r in shown],
            [float(r[column]) for r in shown],
            linestyle="--" if dashed else "-",
            marker=MARKERS[i % len(MARKERS)],
            markersize=4,
            markerfacecolor="none",
            color="black" if dashed else None,
            label=label + (" (reference)" if dashed else ""),
        )


@dataclass(frozen=True)
class ErrorPlot:
    """The error norms vs n, one panel each, with slope guides of the given orders."""

    columns: tuple[str, ...]
    slopes: tuple[int, ...] = (1, 2)
    name: str = "errors"

    def draw(self, rows: Sequence[ResultRow], reference: str) -> Any:
        ncols = min(2, len(self.columns))
        nrows = -(-len(self.columns) // ncols)
        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)
        n = sorted({int(r["n"]) for r in rows})
        for ax, column in zip(axes.flat, self.columns):
            _plot_lines(ax, rows, column, reference)
            # guides through the largest error at the coarsest resolution
            start = max(float(r[column]) for r in rows if int(r["n"]) == n[0])
            for order, style in zip(self.slopes, (":", "-.", (0, (1, 3)))):
                ax.loglog(
                    [n[0], n[-1]],
                    [start, start * (n[0] / n[-1]) ** order],
                    linestyle=style,
                    color="grey",
                    linewidth=1,
                    label=f"order {order}",
                )
            ax.set_xlabel("n (cells per side)")
            ax.set_ylabel(f"{column} [-]" if "Normal" in column else f"{column} [m]")
            ax.set_title(column)
            ax.grid(True, which="both", alpha=0.3)
            ax.legend(fontsize="small")
        for ax in list(axes.flat)[len(self.columns) :]:
            ax.set_visible(False)
        fig.tight_layout()
        return fig


@dataclass(frozen=True)
class TimingPlot:
    """A time column (seconds) vs n, one line per backend."""

    column: str
    label: str
    name: str = ""

    def draw(self, rows: Sequence[ResultRow], reference: str) -> Any:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        _plot_lines(ax, rows, self.column, reference)
        ax.set_xlabel("n (cells per side)")
        ax.set_ylabel(f"{self.label} [s]")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize="small")
        fig.tight_layout()
        return fig


def plot_name(plot: Plot) -> str:
    return plot.name or getattr(plot, "column", "plot")


def draw_all(plots: Sequence[Plot], results: Path, out_dir: Path, reference: str) -> list[Path]:
    """Every plot of ``results`` to ``out_dir/<name>.<png|pdf>``; the written paths."""
    rows = read_results(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for plot in plots:
        fig = plot.draw(rows, reference)
        for fmt in FORMATS:
            path = out_dir / f"{plot_name(plot)}.{fmt}"
            fig.savefig(path, dpi=150)
            written.append(path)
        plt.close(fig)
    return written
