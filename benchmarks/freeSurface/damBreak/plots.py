"""The dam break's plots: the surge front against the experiment and interFoam, deltaT.

``front_<time_step>``: Martin & Moyce's front ``Z`` over ``T`` per mesh and executor, from
collect's histories.csv, with the experiment's means (reference/martin_moyce.csv) and
interFoam's front at the write times (reference/interfoam_front.csv, scaled as
metrics.py does), the obstacle at Z = 2; ``deltaT``: the adaptive time step against
interFoam's (reference/interfoam_time_steps.csv).
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from neofoam_tutorials.suite.plots import histories, history_plot, save

BY = ["mesh", "executor"]
#: the case's column (system/setFields.yaml) and g, for interFoam's front
WIDTH, HEIGHT, G = 0.1461, 0.292, 9.81
OBSTACLE_Z = 0.292 / WIDTH
INTERFOAM_MARKERS = {"x1": "kx", "x2": "k+"}
INTERFOAM_LINES = {"x1": "k--", "x2": "k:"}


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    history = histories()
    for time_step, rows in history.groupby("time_step"):
        save(_front(rows, time_step, references), out / f"front_{time_step}")
    adaptive = history[(history["time_step"] == "adaptive") & (history["Time"] > 0)]
    if not adaptive.empty:
        save(_time_steps(adaptive, references["interfoam_time_steps"]), out / "deltaT")


def _front(history: pd.DataFrame, time_step: str, references: dict[str, pd.DataFrame]) -> Any:
    fig = history_plot(history.assign(Time=history["T"]), "Z", "front Z = x/a [-]", BY, False)
    ax = fig.axes[0]
    experiment = references["martin_moyce"]
    ax.plot(experiment["T_a57mm"], experiment["Z"], "ks", label="Martin & Moyce, a = 57 mm")
    ax.plot(experiment["T_a28mm"], experiment["Z"], "ko", label="Martin & Moyce, a = 28 mm")
    interfoam = references["interfoam_front"]
    for mesh, rows in interfoam[interfoam["time_step"] == time_step].groupby("mesh"):
        if mesh in set(history["mesh"]):
            t = rows["Time"] * np.sqrt(G * HEIGHT) / WIDTH
            ax.plot(t, rows["front"] / WIDTH, INTERFOAM_MARKERS[mesh], label=f"interFoam {mesh}")
    ax.axhline(OBSTACLE_Z, color="grey", linestyle=":", label="obstacle")
    ax.set_xlim(0, history["T"].max())
    ax.set_ylim(0.9, 2.2)
    ax.set_xlabel("T = n t sqrt(g/a) [-]")
    ax.set_title(f"{time_step} time step")
    ax.legend(fontsize="small")
    return fig


def _time_steps(history: pd.DataFrame, interfoam: pd.DataFrame) -> Any:
    fig = history_plot(history, "deltaT", "deltaT [s]", BY, False)
    ax = fig.axes[0]
    for mesh, rows in interfoam.groupby("mesh"):
        if mesh in set(history["mesh"]):
            ax.plot(
                rows["Time"],
                rows["deltaT"],
                INTERFOAM_LINES[mesh],
                linewidth=1,
                label=f"interFoam {mesh}",
            )
    ax.legend(fontsize="small")
    return fig
