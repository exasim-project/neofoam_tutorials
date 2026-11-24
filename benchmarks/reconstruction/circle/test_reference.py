"""The circle benchmark's published reference tables.

numufoam's ``error.csv`` (``reference/numufoam_error.csv``) is the published run of the
case; ``reference/twophaseflow.csv`` is TwoPhaseFlow's reconstructInterface (v2506) run
of it.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from neofoam_tutorials.reconstruction_error import observed_order, read_numufoam

BENCHMARK = Path(__file__).resolve().parent
NUMUFOAM = read_numufoam(BENCHMARK / "reference" / "numufoam_error.csv")
NORMS = ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1")


@pytest.mark.parametrize("norm", NORMS)
def test_numufoam_plicRDF_converges_second_order(norm: str) -> None:
    resolutions = sorted(n for scheme, n in NUMUFOAM if scheme == "plicRDF")
    spacing = np.array([NUMUFOAM["plicRDF", n]["length"] for n in resolutions])
    error = np.array([NUMUFOAM["plicRDF", n][norm] for n in resolutions])

    fitted = -np.polyfit(np.log(1.0 / spacing), np.log(error), 1)[0]
    assert 1.8 < fitted < 2.3, observed_order(spacing, error)


def test_stored_twophaseflow_table_reproduces_numufoam() -> None:
    # numufoam's run agrees to ~1e-10 relative (a different build of the same code)
    with (BENCHMARK / "reference" / "twophaseflow.csv").open(newline="") as file:
        stored = list(csv.DictReader(file))
    assert {int(row["resolution"]) for row in stored} == {8, 16, 32, 64, 128, 256, 512, 1024}
    for row in stored:
        published = NUMUFOAM[row["method"], int(row["resolution"])]
        for norm in (*NORMS, "length", "nCells"):
            assert float(row[norm]) == pytest.approx(published[norm], rel=1e-9), (row, norm)
