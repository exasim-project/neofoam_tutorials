"""The tilted box's plots: the spurious current and the hydrostatic pressure error over time.

``maxU``, ``meanU`` and ``p_err_mean`` over time per mesh and executor, from collect's
histories.csv; TwoPhaseFlow's ``maxU`` at t = 0.01 of the swept meshes
(reference/twophaseflow.csv) as black crosses on the ``maxU`` plot.
"""

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.plots import histories, history_plot, save

BY = ["mesh", "executor"]


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    history = histories()
    history = history[history["Time"] > 0]
    fig = history_plot(history, "maxU", "max |U| [m/s]", BY)
    reference = references["twophaseflow"]
    reference = reference[reference["mesh"].isin(results["mesh"])]
    label = f"TwoPhaseFlow t = 0.01 ({', '.join(reference['mesh'])})"
    fig.axes[0].plot([0.01] * len(reference), reference["maxU_10ms"], "kx", label=label)
    fig.axes[0].legend(fontsize="small")
    save(fig, out / "maxU")
    save(history_plot(history, "meanU", "mean |U| [m/s]", BY), out / "meanU")
    label = "mean |p - p_hydrostatic| / range [-]"
    save(history_plot(history, "p_err_mean", label, BY), out / "p_err_mean")
