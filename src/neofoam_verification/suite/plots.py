"""Plot helpers for a benchmark's ``plots.py`` (``plot(results, references, out)``).

The x axis is a resolution column (``n``, cells per side), both axes logarithmic, one
line per group of cases (``by``: executor and method); a reference table is drawn
dashed black. :func:`history_plot` draws a per-case time series (:func:`histories`, the
cases' ``metrics.dat`` in the workflow directory) instead. :func:`save` writes a figure
as ``<stem>.png`` and ``.pdf``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .workflow import read_table

MARKERS = ("o", "s", "^", "v", "D", "x")
BY = ("executor", "method")
#: a case's metrics table (benchmark.yaml ``metrics``), relative to the workflow directory
METRICS_TABLE = "cases/{case}/postProcessing/metrics.dat"


def _lines(
    ax: Any,
    results: pd.DataFrame,
    column: str,
    x: str,
    by: Sequence[str],
    reference: pd.DataFrame | None,
    reference_label: str,
) -> None:
    for i, (key, rows) in enumerate(results.sort_values(x).groupby(list(by))):
        # log axes: a zero (e.g. a time below the clock's resolution) is left out
        shown = rows[rows[column] > 0]
        ax.loglog(
            shown[x],
            shown[column],
            marker=MARKERS[i % len(MARKERS)],
            markersize=4,
            markerfacecolor="none",
            label=" ".join(map(str, key)),
        )
    if reference is not None and column in reference:
        rows = reference.sort_values(x)
        ax.loglog(rows[x], rows[column], "k--", label=f"{reference_label} (reference)")


def error_plot(
    results: pd.DataFrame,
    columns: Sequence[str],
    reference: pd.DataFrame | None = None,
    reference_label: str = "reference",
    x: str = "n",
    by: Sequence[str] = BY,
    slopes: Sequence[int] = (1, 2),
) -> Any:
    """The error ``columns`` vs ``x``, one panel each, with slope guides of ``slopes``."""
    ncols = min(2, len(columns))
    nrows = -(-len(columns) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)
    n = sorted(results[x].unique())
    for ax, column in zip(axes.flat, columns):
        _lines(ax, results, column, x, by, reference, reference_label)
        # guides through the largest error at the coarsest resolution
        start = results.loc[results[x] == n[0], column].max()
        for order, style in zip(slopes, (":", "-.", (0, (1, 3)))):
            ax.loglog(
                [n[0], n[-1]],
                [start, start * (n[0] / n[-1]) ** order],
                linestyle=style,
                color="grey",
                linewidth=1,
                label=f"order {order}",
            )
        ax.set_xlabel(f"{x} (cells per side)")
        ax.set_ylabel(f"{column} [-]" if "Normal" in column else f"{column} [m]")
        ax.set_title(column)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize="small")
    for ax in list(axes.flat)[len(columns) :]:
        ax.set_visible(False)
    fig.tight_layout()
    return fig


def timing_plot(
    results: pd.DataFrame, column: str, label: str, x: str = "n", by: Sequence[str] = BY
) -> Any:
    """A time ``column`` (seconds) vs ``x``."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    _lines(ax, results, column, x, by, None, "")
    ax.set_xlabel(f"{x} (cells per side)")
    ax.set_ylabel(f"{label} [s]")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize="small")
    fig.tight_layout()
    return fig


def histories(results: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Every case's metrics table, with the case's ``columns`` of ``results`` (its variants)."""
    tables = []
    for row in results[["case", *columns]].itertuples(index=False):
        table = read_table(Path(METRICS_TABLE.format(case=row.case)))
        tables.append(table.assign(**dict(zip(["case", *columns], row))))
    return pd.concat(tables, ignore_index=True)


def history_plot(
    history: pd.DataFrame, column: str, label: str, by: Sequence[str], logy: bool = True
) -> Any:
    """``column`` over ``Time``, one line per ``by`` group (e.g. mesh and executor)."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for i, (key, rows) in enumerate(history.sort_values("Time").groupby(list(by))):
        ax.plot(
            rows["Time"],
            rows[column],
            marker=MARKERS[i % len(MARKERS)],
            markersize=3,
            markerfacecolor="none",
            label=" ".join(map(str, key)),
        )
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel("time [s]")
    ax.set_ylabel(label)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize="small")
    fig.tight_layout()
    return fig


def save(fig: Any, stem: Path) -> None:
    for suffix in (".png", ".pdf"):
        fig.savefig(stem.with_suffix(suffix), dpi=150)
    plt.close(fig)
