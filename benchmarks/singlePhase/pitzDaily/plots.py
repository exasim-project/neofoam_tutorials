"""pitzDaily's plots: the velocity profiles against OpenFOAM, the residuals, the run time.

* ``profiles`` -- Ux / U_inlet over y at x / h = 1, 3, 5, 7 per mesh (the first executor;
  the others agree), from collect's profiles.csv, with OpenFOAM's on
  the same mesh dashed black (reference/openfoam_profiles.csv);
* ``residuals`` -- the initial residuals of Ux and p over the iterations per case (collect's
  histories.csv), the tutorial's tolerances dotted;
* ``reattachment`` -- x_r / h per mesh and executor, with OpenFOAM's and the measured;
* ``wall_time`` -- the wall time of the 1500 iterations per mesh and executor.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from neofoam_verification.suite.plots import MARKERS, histories, history_plot, profiles, save

BY = ["mesh", "executor"]
STATIONS = (1, 3, 5, 7)
STEP, U_INLET = 0.0254, 10.0


def profiles_plot(results: pd.DataFrame, openfoam: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, len(STATIONS), figsize=(12, 4.5), sharey=True)
    first = results[results["executor"] == results["executor"].iloc[0]]
    computed = profiles()
    for row in first.itertuples(index=False):
        profile = computed[computed["case"] == row.case]
        stored = openfoam[openfoam["nCells"] == profile["nCells"].iloc[0]]
        for ax, station in zip(axes, STATIONS):
            ours = profile[profile["x_h"] == station]
            (line,) = ax.plot(ours["Ux"] / U_INLET, ours["y"] / STEP, label=f"{row.case}")
            theirs = stored[stored["x_h"] == station]
            ax.plot(
                theirs["Ux"] / U_INLET,
                theirs["y"] / STEP,
                "--",
                color=line.get_color(),
                alpha=0.8,
                label=f"OpenFOAM {row.mesh}",
            )
    for ax, station in zip(axes, STATIONS):
        ax.axvline(0, color="grey", linewidth=0.5)
        ax.set(title=f"x / h = {station}", xlabel="Ux / U_inlet [-]")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("y / h [-]")
    axes[-1].legend(fontsize="small")
    fig.tight_layout()
    return fig


def reattachment_plot(results: pd.DataFrame, references: dict[str, pd.DataFrame]) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    meshes = list(dict.fromkeys(results["mesh"]))
    for i, (executor, rows) in enumerate(results.groupby("executor")):
        x = [meshes.index(m) + 0.1 * (i - 1) for m in rows["mesh"]]
        ax.plot(x, rows["x_r_h"], MARKERS[i], markerfacecolor="none", label=executor)
    openfoam = references["openfoam"].set_index("mesh").reindex(meshes)
    ax.plot(range(len(meshes)), openfoam["x_r_h"], "k_", markersize=20, label="OpenFOAM")
    measured = float(references["pitz_daily_1983"]["x_r_h"].iloc[0])
    ax.axhline(measured, color="grey", linestyle=":", label="Pitz & Daily 1983")
    ax.set_xticks(range(len(meshes)), meshes)
    ax.set(xlabel="mesh", ylabel="reattachment length x_r / h [-]")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize="small")
    fig.tight_layout()
    return fig


def wall_time_plot(results: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    meshes = list(dict.fromkeys(results["mesh"]))
    for i, (executor, rows) in enumerate(results.groupby("executor")):
        x = [meshes.index(m) for m in rows["mesh"]]
        ax.semilogy(x, rows["wall_s"], marker=MARKERS[i], markerfacecolor="none", label=executor)
    ax.set_xticks(range(len(meshes)), meshes)
    ax.set(xlabel="mesh", ylabel="wall time of the run [s]")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize="small")
    fig.tight_layout()
    return fig


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    save(profiles_plot(results, references["openfoam_profiles"]), out / "profiles")
    history = histories()
    fig = history_plot(history, "Ux_res", "initial residual", BY)
    ax = fig.axes[0]
    for i, (_, rows) in enumerate(history.sort_values("Time").groupby(BY)):
        ax.plot(rows["Time"], rows["p_res"], color=ax.lines[i].get_color(), linestyle="--")
    ax.axhline(1e-3, color="grey", linestyle=":")
    ax.axhline(1e-2, color="grey", linestyle=":")
    for line in ax.lines:
        line.set_marker("")
    ax.set(xlabel="SIMPLE iteration", title="Ux (solid) and p (dashed)")
    ax.legend(ax.lines[: len(ax.lines) // 2 - 1], [" ".join(k) for k, _ in history.groupby(BY)])
    save(fig, out / "residuals")
    save(reattachment_plot(results, references), out / "reattachment")
    save(wall_time_plot(results), out / "wall_time")
