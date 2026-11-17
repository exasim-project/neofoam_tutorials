"""The benchmark suite: the circle benchmark's definition, its stored reference table and,
marked ``openfoam``, a smoke run of its Snakemake workflow on TwoPhaseFlow and the
NeoFOAM backend's alpha samples against reconstructInterface's own."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from foamlib import FoamFile

from neofoam_verification import run
from neofoam_verification.solvers.reconstruction_io import alpha_samples
from neofoam_verification.suite import backends
from neofoam_verification.suite.benchmark import cases, discover, load
from neofoam_verification.suite.checks import Result, read_table
from neofoam_verification.suite.workflow import export, generate

ROOT = Path(__file__).resolve().parents[1]
CIRCLE = ROOT / "benchmarks" / "reconstruction" / "circle"
BENCHMARK = load(CIRCLE / "benchmark.py")


def test_discovery_finds_the_circle_benchmark() -> None:
    assert CIRCLE / "benchmark.py" in discover(ROOT / "benchmarks")
    assert BENCHMARK.name == "reconstruction/circle"


def test_method_override_names_the_cases(tmp_path: Path) -> None:
    sweep = cases(BENCHMARK, methods=["myScheme"], smoke=True)

    assert [c.name for c in sweep] == ["myScheme_n8", "myScheme_n16"]
    assert sweep[0].parameters == {"nx": 8, "nz": 8, "reconScheme": "myScheme"}
    snakefile = export(BENCHMARK, tmp_path, sweep, ["twophaseflow"], {}, smoke=True).read_text()
    for rule in ("generate", "blockMesh", "setAlphaField", "alphaSamples", "solve", "table"):
        assert f"rule {rule}:" in snakefile
    config = json.loads(
        (tmp_path / "configs" / "myScheme_n8" / "simulation_parameters.json").read_text()
    )
    assert config == {"simulation_parameters": {"nx": 8, "nz": 8, "reconScheme": "myScheme"}}


def test_stored_twophaseflow_table_passes_the_checks() -> None:
    stored = read_table(CIRCLE / "reference" / "twophaseflow.csv")
    results = [Result("twophaseflow", m, n, values) for (m, n), values in stored.items()]
    assert {n for _, n in stored} == set(BENCHMARK.sweep.resolutions)

    outcome = [r for check in BENCHMARK.checks for r in check.evaluate(BENCHMARK, results)]
    assert {r.status for r in outcome} == {"pass"}, outcome


def _have(bashrc: Path, command: str) -> bool:
    return bashrc.is_file() and backends._has_command(bashrc, command)


TWOPHASEFLOW = backends.BACKENDS["twophaseflow"]
NEOFOAM = backends.BACKENDS["neofoam"]


@pytest.mark.openfoam
@pytest.mark.skipif(
    not _have(TWOPHASEFLOW.bashrc, "reconstructInterface"),
    reason="no TwoPhaseFlow reconstructInterface",
)
def test_smoke_run_of_the_reference(tmp_path: Path) -> None:
    code = run.main(
        [str(CIRCLE), "--smoke", "--backend", "twophaseflow", "--results", str(tmp_path), "-j", "2"]
    )

    assert code == 0
    checks = json.loads((tmp_path / "reconstruction" / "circle" / "checks.json").read_text())[
        "checks"
    ]
    assert {c["status"] for c in checks} == {"pass"}, checks
    assert (tmp_path / "summary.md").is_file()


@pytest.mark.openfoam
@pytest.mark.skipif(
    not (
        _have(TWOPHASEFLOW.bashrc, "reconstructInterface")
        and _have(NEOFOAM.bashrc, "setAlphaField")
    ),
    reason="no TwoPhaseFlow reconstructInterface or OpenFOAM-v2406 setAlphaField",
)
def test_alpha_samples_are_reconstructInterface_samples(tmp_path: Path) -> None:
    (case,) = [c for c in cases(BENCHMARK, smoke=True) if c.resolution == 8]
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"simulation_parameters": case.parameters}))
    directory = tmp_path / "case"
    generate(BENCHMARK, config, directory)
    backends.run(NEOFOAM, directory, "blockMesh", "log.blockMesh")
    commands = alpha_samples(directory)
    for i, command in enumerate(commands):
        backends.run(NEOFOAM, directory, command, f"log.alphaSamples.{i}")
    backends.run(TWOPHASEFLOW, directory, "reconstructInterface", "log.reconstructInterface")

    # reconstructInterface writes the last sample's alpha after its single time step
    expected = FoamFile(directory / "0.001" / "alpha1")["internalField"]
    np.testing.assert_array_equal(
        FoamFile(directory / str(len(commands)) / "alpha1")["internalField"], expected
    )


def test_in_process_runner_is_deferred() -> None:
    with pytest.raises(NotImplementedError):
        run.main([str(CIRCLE), "--in-process"])


@pytest.mark.backend
@pytest.mark.skipif(
    NEOFOAM.unavailable("reconstructInterface") is not None
    or not _have(NEOFOAM.bashrc, "setAlphaField"),
    reason=f"neofoam backend: {NEOFOAM.unavailable('reconstructInterface')}",
)
def test_smoke_run_of_neofoam_matches_the_reference(tmp_path: Path) -> None:
    code = run.main(
        [str(CIRCLE), "--smoke", "--backend", "neofoam", "--results", str(tmp_path), "-j", "2"]
    )

    assert code == 0
    checks = json.loads((tmp_path / "reconstruction" / "circle" / "checks.json").read_text())
    assert {c["status"] for c in checks["checks"]} == {"pass"}, checks
