"""The discUniFlow benchmark's smoke variants."""

from __future__ import annotations

from pathlib import Path

from neofoam_tutorials.suite.benchmark import dimensions, load

PAPER = Path(__file__).resolve().parent


def test_smoke_run_sweeps_the_coarsest_mesh_one_cfl_serial_and_both_methods() -> None:
    dims = dimensions(load(PAPER), smoke=True)

    assert list(dims["mesh"]) == ["n10"]
    assert dims["control_dict_config"] == {"CFL01": {"maxAlphaCo": 0.1}}
    assert list(dims["neo_n_control_config"]) == ["Serial"]
    assert list(dims["advection_scheme_config"]) == ["isoAdvector", "MULES"]
