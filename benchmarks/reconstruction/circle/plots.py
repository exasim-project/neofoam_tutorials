"""The circle benchmark's plots: the error norms, k1 and the solver wall time vs n.

TwoPhaseFlow's stored table is the dashed reference of the error plot (it holds no
timings: its k1 is CPU time with 1 ms resolution).
"""

from pathlib import Path

import pandas as pd

from neofoam_verification.suite.plots import error_plot, save, timing_plot

NORMS = ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1")


def plot(results: pd.DataFrame, references: dict[str, pd.DataFrame], out: Path) -> None:
    results = results.assign(n=results["mesh"].str.removeprefix("n").astype(int))
    reference = references["twophaseflow"].rename(columns={"resolution": "n"})
    reference = reference[reference["method"].isin(results["method"])]
    reference = reference[reference["n"].isin(results["n"])]
    save(error_plot(results, NORMS, reference, "TwoPhaseFlow"), out / "errors")
    save(timing_plot(results, "k1", "reconstruction time per sample, k1"), out / "k1")
    save(timing_plot(results, "wall_s", "solver wall time"), out / "wall")
