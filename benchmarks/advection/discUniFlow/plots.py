"""The discUniFlow plots: E1 vs n per CFL, E1 vs CFL per method, the time per step.

numufoam's error.csv (isoAlpha, plicRDF, MULES; dashed) is the reference: its MULES is
the same scheme up to the interface normal's gradient, its isoAlpha and plicRDF are
other reconstructions than NeoFOAM's gradAlpha, so only their trends compare.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from neofoam_verification.suite.plots import save

MARKERS = {"Serial": "o", "CPU": "s", "GPU": "^"}
COLOURS = {"isoAdvector": "C0", "MULES": "C1"}
REFERENCE = {"isoAlpha": "0.6", "plicRDF": "0.35", "MULES": "k"}


def _cfl(label: str) -> float:
    """``CFL005`` -> 0.05, ``CFL05`` -> 0.5."""
    digits = label.removeprefix("CFL")
    return float(digits[0] + "." + digits[1:])


def _with_n(table: pd.DataFrame) -> pd.DataFrame:
    return table.assign(n=table["mesh"].str.removeprefix("n").astype(int))


def _loglog_axes(ax: plt.Axes, xlabel: str, ylabel: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize="x-small")


def error_vs_n(results: pd.DataFrame, reference: pd.DataFrame) -> plt.Figure:
    cfls = sorted(results["CFL"].unique(), key=_cfl)
    fig, axes = plt.subplots(1, len(cfls), figsize=(4.5 * len(cfls), 4), squeeze=False)
    for ax, cfl in zip(axes.flat, cfls):
        rows = results[results["CFL"] == cfl].sort_values("n")
        for (method, executor), line in rows.groupby(["method", "executor"]):
            ax.loglog(
                line["n"],
                line["Eshape"],
                marker=MARKERS.get(executor, "x"),
                color=COLOURS.get(method),
                markerfacecolor="none",
                label=f"{method} {executor}",
            )
        ref = reference[reference["CFL"] == cfl].sort_values("n")
        for method, line in ref.groupby("method"):
            ax.loglog(
                line["n"],
                line["Eshape"],
                "--",
                color=REFERENCE.get(method, "k"),
                label=f"numufoam {method}",
            )
        n0, n1 = rows["n"].min(), rows["n"].max()
        start = rows.loc[rows["n"] == n0, "Eshape"].max()
        for order, style in ((1, ":"), (2, "-.")):
            ax.loglog([n0, n1], [start, start * (n0 / n1) ** order], style, color="grey")
            ax.annotate(f"order {order}", (n1, start * (n0 / n1) ** order), fontsize="x-small")
        ax.set_title(f"maxAlphaCo {_cfl(cfl):g}")
        _loglog_axes(ax, "n (cells per side)", "E1 at t = 0.5 [m$^3$]")
    fig.tight_layout()
    return fig


def error_vs_cfl(results: pd.DataFrame, reference: pd.DataFrame) -> plt.Figure:
    methods = sorted(results["method"].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 4), squeeze=False)
    serial = results[results["executor"] == results["executor"].iloc[0]]
    for ax, method in zip(axes.flat, methods):
        rows = serial[serial["method"] == method].assign(cfl=lambda t: t["CFL"].map(_cfl))
        for i, (n, line) in enumerate(rows.sort_values("cfl").groupby("n")):
            ax.loglog(line["cfl"], line["Eshape"], marker="o", color=f"C{i}", label=f"n {n}")
            ref = reference[(reference["method"] == method) & (reference["n"] == n)]
            ref = ref.assign(cfl=ref["CFL"].map(_cfl)).sort_values("cfl")
            ax.loglog(ref["cfl"], ref["Eshape"], "--", color=f"C{i}")
        dashed = "; dashed: numufoam's" if method in set(reference["method"]) else ""
        ax.set_title(f"{method} ({serial['executor'].iloc[0]}){dashed}")
        _loglog_axes(ax, "maxAlphaCo", "E1 at t = 0.5 [m$^3$]")
    fig.tight_layout()
    return fig


def time_per_step(results: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    rows = results.assign(step_s=results["wall_s"] / results["steps"])
    for ax, column, label in (
        (axes[0], "Tadv", "alpha advection per step [s]"),
        (axes[1], "step_s", "solver wall time per step [s]"),
    ):
        # the cost of a step does not depend on the CFL: its mean over the CFLs
        mean = rows.groupby(["method", "executor", "n"], as_index=False)[column].mean()
        for (method, executor), line in mean.groupby(["method", "executor"]):
            ax.loglog(
                line["n"],
                line[column],
                marker=MARKERS.get(executor, "x"),
                color=COLOURS.get(method),
                markerfacecolor="none",
                label=f"{method} {executor}",
            )
        _loglog_axes(ax, "n (cells per side)", label)
    fig.tight_layout()
    return fig


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    results = _with_n(results)
    reference = _with_n(references["numufoam"])
    reference = reference[reference["n"].isin(results["n"]) & reference["CFL"].isin(results["CFL"])]
    save(error_vs_n(results, reference), out / "E1_vs_n")
    save(error_vs_cfl(results, reference), out / "E1_vs_CFL")
    save(time_per_step(results), out / "time_per_step")
