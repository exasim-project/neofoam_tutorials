"""The swept variants of a smoke and ``--method`` run, on the circle benchmark's files."""

from __future__ import annotations

from pathlib import Path

from neofoam_tutorials.suite.benchmark import dimensions, load, name

CIRCLE = Path(__file__).resolve().parents[2] / "benchmarks" / "reconstruction" / "circle"
SPEC = load(CIRCLE)


def test_smoke_method_run_sweeps_the_smoke_variants_and_the_method() -> None:
    dims = dimensions(SPEC, smoke=True, methods=["myScheme"])

    assert name(CIRCLE) == "reconstruction/circle"
    assert list(dims["mesh"]) == ["n8", "n16"]
    assert dims["neo_n_control_config"] == {"Serial": {"executor": "Serial"}}
    assert dims["reconstruction_scheme_config"] == {
        "myScheme": {"reconstructionScheme": "myScheme"}
    }
