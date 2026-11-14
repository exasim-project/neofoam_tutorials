"""The registry and the case files describe the same benchmark (no OpenFOAM needed)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from foamlib import FoamFile

from neofoam_verification.benchmarks import (
    BENCHMARKS,
    Benchmark,
    GeneratedVelocity,
    UniformVelocity,
)

UNIFORM = {n: b for n, b in BENCHMARKS.items() if isinstance(b.velocity, UniformVelocity)}
GENERATED = {n: b for n, b in BENCHMARKS.items() if isinstance(b.velocity, GeneratedVelocity)}


@pytest.mark.parametrize("benchmark", UNIFORM.values(), ids=UNIFORM.keys())
def test_registry_velocity_matches_initial_U(benchmark: Benchmark) -> None:
    assert isinstance(benchmark.velocity, UniformVelocity)
    U = FoamFile(benchmark.case_dir / "0.orig" / "U")["internalField"]
    np.testing.assert_array_equal(U, benchmark.velocity.value)


@pytest.mark.parametrize("benchmark", GENERATED.values(), ids=GENERATED.keys())
def test_registry_velocity_matches_isoAdvector_dict(benchmark: Benchmark) -> None:
    velocity = benchmark.velocity
    assert isinstance(velocity, GeneratedVelocity)
    d = FoamFile(benchmark.case_dir / "system" / "fvSolution")["isoAdvector"]
    expected = {
        "period": velocity.period,
        "spirallingFlow": velocity.spiralling_flow,
        "reverseTime": velocity.reverse_time,
    }
    assert {key: d.get(key, 0.0) for key in expected} == expected


@pytest.mark.parametrize("benchmark", GENERATED.values(), ids=GENERATED.keys())
def test_registry_generator_is_the_case_application(benchmark: Benchmark) -> None:
    assert isinstance(benchmark.velocity, GeneratedVelocity)
    make_files = benchmark.case_dir / benchmark.velocity.generator / "Make" / "files"
    assert f"$(FOAM_USER_APPBIN)/{benchmark.velocity.generator}" in make_files.read_text()


@pytest.mark.parametrize("benchmark", BENCHMARKS.values(), ids=BENCHMARKS.keys())
def test_registry_shape_matches_setAlphaFieldDict(benchmark: Benchmark) -> None:
    d = FoamFile(benchmark.case_dir / "system" / "setAlphaFieldDict")
    assert d["type"] == type(benchmark.shape).__name__.lower()
    for field in dataclasses.fields(benchmark.shape):
        if field.name != "scale":
            value = getattr(benchmark.shape, field.name)
            np.testing.assert_array_equal(d[field.name], value, err_msg=field.name)


@pytest.mark.parametrize("benchmark", BENCHMARKS.values(), ids=BENCHMARKS.keys())
def test_registry_times_match_controlDict(benchmark: Benchmark) -> None:
    d = FoamFile(benchmark.case_dir / "system" / "controlDict")
    assert (d["endTime"], d["writeInterval"]) == (benchmark.end_time, benchmark.write_interval)
    fo = d["functions"]["volumeFractionError"]
    assert fo["functionType"] == type(benchmark.shape).__name__.lower()
    np.testing.assert_array_equal(fo["origin"], benchmark.shape.origin)
    assert fo["radius"] == benchmark.shape.radius


@pytest.mark.parametrize("benchmark", BENCHMARKS.values(), ids=BENCHMARKS.keys())
def test_default_resolution_is_the_case_blockMeshDict(benchmark: Benchmark) -> None:
    d = FoamFile(benchmark.case_dir / "system" / "blockMeshDict")
    for key, value in benchmark.resolutions[benchmark.default_resolution].items():
        assert d[key] == value
