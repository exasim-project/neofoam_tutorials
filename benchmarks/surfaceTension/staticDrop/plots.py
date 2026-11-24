"""The static drop's plots: the spurious current over time and the pressure jump vs mesh.

``maxU`` (and ``meanU``) over time per mesh and executor, from collect's histories.csv;
the end time's Laplace pressure jump ``dp`` per mesh against ``sigma/R``, with interFoam's
jump (reference/interfoam.csv, n40) and the relative error ``dp_err``.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from neofoam_tutorials.suite.plots import MARKERS, histories, history_plot, save

BY = ["mesh", "executor"]


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    history = histories()
    history = history[history["Time"] > 0]
    save(history_plot(history, "maxU", "max |U| [m/s]", BY), out / "maxU")
    save(history_plot(history, "meanU", "mean |U| [m/s]", BY), out / "meanU")

    results = results.assign(n=results["mesh"].str.removeprefix("n").astype(int))
    fig, (jump, error) = plt.subplots(1, 2, figsize=(10, 4))
    for i, (executor, rows) in enumerate(results.sort_values("n").groupby("executor")):
        style = {"marker": MARKERS[i % len(MARKERS)], "markerfacecolor": "none"}
        jump.plot(rows["n"], rows["dp"], label=f"dp {executor}", **style)
        error.loglog(rows["n"], rows["dp_err"], label=executor, **style)
    rows = results.drop_duplicates("n").sort_values("n")
    jump.plot(rows["n"], rows["sigma_R"], "k--", label="sigma/R")
    interfoam = references["interfoam"].assign(n=lambda t: t["mesh"].str[1:].astype(int))
    jump.plot(interfoam["n"], interfoam["dp"], "kx", markersize=8, label="interFoam")
    jump.set_ylabel("pressure jump [Pa]")
    error.set_ylabel("|dp / (sigma/R) - 1| [-]")
    for ax in (jump, error):
        ax.set_xlabel("n (cells per side)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize="small")
    fig.tight_layout()
    save(fig, out / "pressure_jump")
