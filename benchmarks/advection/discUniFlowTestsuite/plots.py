"""The discUniFlow testsuite plots: E1 at t = 4 and the time per step, per executor.

TwoPhaseFlow's stored advectorVoF runs (same schemes) are the dashed references.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from neofoam_tutorials.suite.plots import save

COLOURS = {"isoAdvector": "C0", "MULES": "C1"}


def _per_executor(ax: plt.Axes, results: pd.DataFrame, column: str) -> None:
    executors = list(dict.fromkeys(results["executor"]))
    for method, rows in results.groupby("method"):
        x = [executors.index(e) for e in rows["executor"]]
        ax.plot(x, rows[column], "o", color=COLOURS.get(method), label=method)
    ax.set_xticks(range(len(executors)), executors)
    ax.grid(True, alpha=0.3)


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    _per_executor(axes[0], results, "Eshape")
    for name, reference in references.items():
        for _, row in reference.iterrows():
            axes[0].axhline(
                row["Eshape"],
                linestyle="--",
                color=COLOURS.get(row["method"], "k"),
                label=f"TwoPhaseFlow {row['method']} ({name})",
            )
    axes[0].set_ylabel("E1 at t = 4 [m$^3$]")
    axes[0].legend(fontsize="x-small")
    _per_executor(axes[1], results.assign(step_s=results["wall_s"] / results["steps"]), "step_s")
    axes[1].set_yscale("log")
    axes[1].set_ylabel("solver wall time per step [s]")
    axes[1].legend(fontsize="x-small")
    fig.tight_layout()
    save(fig, out / "E1_and_time")
