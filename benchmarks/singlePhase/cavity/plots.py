"""The cavity's plots: the centreline profiles against Ghia, the errors, the run times.

* ``profiles`` -- u(0.5, y) and v(x, 0.5) of each mesh (the first executor; the others
  agree), from collect's profiles.csv, with Ghia et al. (1982) as
  black circles (reference/ghia1982.csv);
* ``error_vs_n`` -- the L2 and Linf centreline errors against Ghia over n, with OpenFOAM's
  icoFoam on the same meshes dashed black (reference/icofoam.csv);
* ``wall_time``, ``time_per_step`` -- the run's wall time and wall time per step over n.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from neofoam_verification.suite.plots import error_plot, profiles, save, timing_plot

BY = ["executor"]


def profiles_plot(results: pd.DataFrame, ghia: pd.DataFrame) -> plt.Figure:
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.5))
    first = results[results["executor"] == results["executor"].iloc[0]]
    stored = profiles()
    for row in first.itertuples(index=False):
        profile = stored[stored["case"] == row.case]
        label = f"{row.mesh} {row.executor}"
        left.plot(profile["u"], profile["y"], label=label)
        right.plot(profile["x"], profile["v"], label=label)
    left.plot(ghia["u"], ghia["y"], "ko", markerfacecolor="none", label="Ghia et al. 1982")
    right.plot(ghia["x"], ghia["v"], "ko", markerfacecolor="none", label="Ghia et al. 1982")
    left.set(xlabel="u at x = 0.5 [m/s]", ylabel="y [m]", title="vertical centreline")
    right.set(xlabel="x [m]", ylabel="v at y = 0.5 [m/s]", title="horizontal centreline")
    for ax in (left, right):
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize="small")
    fig.tight_layout()
    return fig


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    results = results.assign(n=(1.0 / results["h"]).round().astype(int))
    save(profiles_plot(results, references["ghia1982"]), out / "profiles")
    icofoam = references["icofoam"]
    icofoam = icofoam.assign(n=icofoam["mesh"].str[1:].astype(int))
    columns = ["u_L2", "u_Linf", "v_L2", "v_Linf"]
    fig = error_plot(results, columns, icofoam, "OpenFOAM icoFoam", by=BY)
    for ax in fig.axes:
        ax.set_ylabel(f"{ax.get_title()} against Ghia [m/s]")
    save(fig, out / "error_vs_n")
    save(timing_plot(results, "wall_s", "wall time", by=BY), out / "wall_time")
    save(
        timing_plot(results, "time_per_step_s", "wall time per step", by=BY), out / "time_per_step"
    )
