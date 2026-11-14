"""The benchmark registry: each TwoPhaseFlow advection case as data.

A benchmark is a case directory under ``cases/<name>`` (OpenFOAM format: blockMeshDict,
``0.orig``, setAlphaFieldDict, the MULES controls in fvSolution/fvSchemes, controlDict
with end time, write interval and maxAlphaCo) plus what the metrics need to know
about it: the initial shape, the prescribed velocity and the resolutions.
``tests/test_benchmarks.py`` checks that the registry and the case files agree.

Adding a benchmark (sinWave, tiltedBox) is a case directory plus an entry in
``BENCHMARKS``.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from foamlib import FoamFile

from .shapes import Cylinder, Shape, Sphere

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

    @property
    def write_times(self) -> list[float]:
        n = round(self.end_time / self.write_interval)
        return [i * self.write_interval for i in range(n + 1)]

    def copy_case(self, dest: Path, resolution: str | None = None) -> Path:
        """Copy the case to ``dest`` with the blockMeshDict entries of ``resolution``."""
        shutil.copytree(self.case_dir, dest)
        block_mesh_dict = FoamFile(dest / "system" / "blockMeshDict")
        for key, value in self.resolutions[resolution or self.default_resolution].items():
            block_mesh_dict[key] = value
        return dest


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

VORTEX_SHEARED_DISC = Benchmark(
    name="vortexShearedDisc",
    # test-vortexShearedDisc: a disc of radius 0.15 at (0.5, 0.75) in the unit square
    # (x-z), stretched by the single vortex psi = sin^2(pi x) sin^2(pi z)/pi; phi is the
    # stream function's point-value line integral (generateUVortex2D), divergence-free to
    # round-off. The flow reverses at t = 4 and the disc is back at t = 8.
    shape=Cylinder(origin=(0.5, 0.0, 0.75), radius=0.15, direction=(0.0, 1.0, 0.0)),
    velocity=GeneratedVelocity("generateUVortex2D", period=16.0),
    end_time=8.0,
    write_interval=4.0,
    # the testsuite runs 32 ... 512 cells per side
    resolutions={f"{n}x{n}": {"nx": n, "nz": n} for n in (32, 64, 128, 256)},
    default_resolution="128x128",
)

DEFORMATION_SPHERE = Benchmark(
    name="deformationSphere",
    # test-deformationSphere: a sphere of radius 0.15 at (0.5, 0.75, 0.25) in a
    # 1 x 1 x 2 box, the single vortex in x-y plus w = (1 - 2r)^2 along z
    # (generateUDeform: face-centre velocity, then CorrectPhi), reversed at t = 1.5.
    shape=Sphere(origin=(0.5, 0.75, 0.25), radius=0.15),
    velocity=GeneratedVelocity("generateUDeform", spiralling_flow=3.0),
    end_time=3.0,
    write_interval=1.5,
    # the testsuite runs res x res x 2 res, res = 32, 64, 128; 64 would store 12 MB of alpha
    resolutions={"32x32x64": {"nx": 32, "ny": 32, "nz": 64}},
    default_resolution="32x32x64",
)

LEVEQUE = Benchmark(
    name="Leveque",
    # test-Leveque: LeVeque's 3D deformation of a sphere of radius 0.15 at
    # (0.35, 0.35, 0.35) in the unit cube (generateU: face-centre velocity, then
    # CorrectPhi), reversed at t = 1.5.
    shape=Sphere(origin=(0.35, 0.35, 0.35), radius=0.15),
    velocity=GeneratedVelocity("generateU", spiralling_flow=3.0),
    end_time=3.0,
    write_interval=1.5,
    # the testsuite runs res^3, res = 32, 64, 128; 64 would store 6 MB of alpha
    resolutions={"32x32x32": {"nx": 32, "ny": 32, "nz": 32}},
    default_resolution="32x32x32",
)

BENCHMARKS: dict[str, Benchmark] = {
    b.name: b for b in (DISC_UNI_FLOW, VORTEX_SHEARED_DISC, DEFORMATION_SPHERE, LEVEQUE)
}
