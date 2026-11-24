"""The discUniFlow benchmark's files: the smoke variants, and the checks of its
``benchmark.yaml`` on the stored numufoam table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.suite.benchmark import dimensions, load
from neofoam_tutorials.suite.checks import evaluate

PAPER = Path(__file__).resolve().parent


def _as_results(stored: pd.DataFrame) -> pd.DataFrame:
    """A stored table as the Serial rows of a ``results.csv``."""
    return stored.assign(
        case=[f"{m}_{c}" for m, c in zip(stored["method"], stored.get("CFL", stored["mesh"]))],
        executor="Serial",
    )


def test_smoke_run_sweeps_the_coarsest_mesh_one_cfl_serial_and_both_methods() -> None:
    dims = dimensions(load(PAPER), smoke=True)

    assert list(dims["mesh"]) == ["n10"]
    assert dims["control_dict_config"] == {"CFL01": {"maxAlphaCo": 0.1}}
    assert list(dims["neo_n_control_config"]) == ["Serial"]
    assert list(dims["advection_scheme_config"]) == ["isoAdvector", "MULES"]


def test_numufoam_mules_passes_the_checks_and_where_limits_the_bound_check() -> None:
    stored = pd.read_csv(PAPER / "reference" / "numufoam.csv")
    mules = _as_results(stored[stored["method"] == "MULES"])

    results = evaluate(
        load(PAPER)["checks"], mules, PAPER / "reference", ["CFL", "executor", "method"]
    )

    statuses = {(r["check"], r["group"]): r["status"] for r in results}
    assert set(statuses.values()) == {"pass"}, results
    for cfl in ("CFL005", "CFL01", "CFL02", "CFL05"):
        reference = [
            s
            for (c, g), s in statuses.items()
            if c.startswith("reference numufoam.csv") and g == f"{cfl} Serial MULES"
        ]
        assert reference == ["pass"]
    # numufoam's MULES overshoots at CFL 0.2 and 0.5: not held to the bound
    bounded = {g for c, g in statuses if c == "maximum Ebound"}
    assert bounded == {"CFL005 Serial MULES", "CFL01 Serial MULES"}
