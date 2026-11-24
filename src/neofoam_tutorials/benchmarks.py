"""The benchmark registry: each TwoPhaseFlow advection case as data.

A benchmark is a case directory under ``cases/<name>`` (OpenFOAM format: blockMeshDict,
``0.orig``, setAlphaFieldDict, the MULES controls in fvSolution/fvSchemes, controlDict
with end time, write interval and maxAlphaCo) plus what the metrics need to know
about it: the initial shape, the prescribed velocity and the resolutions.
``test/test_benchmarks.py`` checks that the registry and the case files agree.

Adding a benchmark (sinWave, tiltedBox) is a case directory plus an entry in
``BENCHMARKS``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .shapes import Cylinder, Shape

CASES = Path(__file__).resolve().parents[2] / "cases"


@dataclass(frozen=True)
class UniformVelocity:
    """A velocity constant in space and time: ``U`` internal field, ``phi = U_f . S_f``."""

    value: tuple[float, float, float]


@dataclass(frozen=True)
class GeneratedVelocity:
    """A velocity field written by one of the testsuite's generator applications.

    ``generator`` is the OpenFOAM application in ``cases/<name>/<generator>/`` that
    writes ``0/U`` and ``0/phi`` (``phi0``) on the meshed case. advectorVoF and the
    library read that ``phi`` and make it time-dependent through the ``isoAdvector``
    dict of system/fvSolution: ``reverse_time`` negates it once ``t >= reverseTime``,
    then ``phi = phi0 cos(2 pi (t + dt/2)/period)`` or, with ``spiralling_flow``,
    ``phi = phi0 cos(pi (t + dt/2)/spirallingFlow)`` (0: off). The flows return to the
    initial shape at the end time.
    """

    generator: str
    period: float = 0.0
    spiralling_flow: float = 0.0
    reverse_time: float = 0.0


Velocity = UniformVelocity | GeneratedVelocity


@dataclass(frozen=True)
class Benchmark:
    name: str
    shape: Shape
    velocity: Velocity
    end_time: float
    write_interval: float
    # blockMeshDict entries per resolution
    resolutions: dict[str, dict[str, int]]
    default_resolution: str

    @property
    def case_dir(self) -> Path:
        return CASES / self.name


DISC_UNI_FLOW = Benchmark(
    name="discUniFlow",
    # TwoPhaseFlow testsuite/advection/test-discUniFlow: a disc of radius 0.25 at
    # (0.5, 0.5) in a 5 x 3 domain (x-z, one cell in y) translated diagonally.
    shape=Cylinder(origin=(0.5, 0.0, 0.5), radius=0.25, direction=(0.0, 1.0, 0.0)),
    velocity=UniformVelocity((1.0, 0.0, 0.5)),
    end_time=4.0,
    write_interval=1.0,
    # the testsuite runs one resolution: dx = dz = 0.05, 10 cells per disc diameter
    resolutions={"100x60": {"nx": 100, "nz": 60}},
    default_resolution="100x60",
)

BENCHMARKS: dict[str, Benchmark] = {b.name: b for b in (DISC_UNI_FLOW,)}
