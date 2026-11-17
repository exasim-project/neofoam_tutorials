"""``neofoam solver reconstructInterface``: TwoPhaseFlow's reconstructInterface on NeoFOAM.

Reads the alpha samples NeoFOAM's ``setAlphaField`` tool wrote (``samples: N``: time
directories 1 ... N, :mod:`.reconstruction_io`), reconstructs each with the
``reconstructionSchemeNeoN`` member named by ``solvers.<alpha>.reconstructionScheme``
(any registered one, ``neofoam.plugins`` included) on the ``executor`` of
``system/controlDict``, and writes ``reconstructionError``'s ``error.dat``
(:mod:`..reconstruction_error`); ``k1`` is the mean wall time of a reconstruction (copy
of normal and centre to the host included), after one untimed warm-up on the first
sample, which builds the stencils (~2 s at x1024). ``timing.dat`` beside it holds the
wall time of the whole run (``wall_s``, from the solver's start, imports excluded).

A ``neofoam.solvers`` entry point (pyproject): this module exports the
``reconstructInterface`` spec, with the configs a sweep varies (mesh, executor, scheme),
and ``run(argv)``.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from foamlib import FoamFile
from neofoam.framework.solver import Solver
from neofoam.framework.tools import PreprocessConfig
from neofoam.io import OF, BaseConfig, IOStrategy
from neofoam.solver.neon_runtime import NeoNControlConfig
from neofoam.tools.block_mesh import BlockMeshDictConfig
from pydantic import ConfigDict

from ..reconstruction_error import ReconstructionError, sample_errors
from .reconstruction_io import (
    alpha_name,
    sample_centres,
    sample_shape,
    write_error_dat,
    write_timing_dat,
)


@IOStrategy(OF("system/fvSolution", subdict="solvers.alpha1"))
class ReconstructionSchemeConfig(BaseConfig):  # type: ignore[misc]
    """``solvers.alpha1.reconstructionScheme`` of ``system/fvSolution``: the scheme run.

    Example::

        solvers { alpha1 { reconstructionScheme gradAlpha; } }

    The other ``solvers.alpha1`` entries (``isoFaceTol`` ...) are kept: a merged payload
    rewrites the whole ``solvers`` dict.
    """

    model_config = ConfigDict(extra="allow")

    reconstructionScheme: str = "gradAlpha"


reconstructInterface = Solver("reconstructInterface")
for _config in (
    PreprocessConfig,
    BlockMeshDictConfig,
    NeoNControlConfig,
    ReconstructionSchemeConfig,
):
    reconstructInterface.config(_config)


def run(argv: list[str]) -> None:
    """Reconstruct every sample of the case (``-case DIR``, default the working directory)."""
    start_run = time.perf_counter()
    import pybFoam as pyf
    from neofoam import neofoam_bindings as nfb
    from neofoam.algorithms.geometric_vof import NeoNCellCutOps
    from neofoam.solver.incompressibleVoFNeoN.models.alpha_advection.iso_advector import (
        read_iso_advector_controls,
    )
    from neofoam.solver.incompressibleVoFNeoN.models.reconstruction import (
        reconstructionSchemeNeoN,
    )
    from neofoam.solver.neon_runtime import ensure_neon_initialized, requested_executor

    if "-case" in argv:
        os.chdir(argv[argv.index("-case") + 1])
    case = Path.cwd()
    name = alpha_name(case)
    ensure_neon_initialized(["reconstructInterface"])
    arg_list = pyf.argList(["reconstructInterface", "-noFunctionObjects"])
    foam_time = pyf.Time(arg_list)  # arg_list must outlive it
    executor = requested_executor()
    runtime = nfb.create_adapter_run_time(foam_time, executor)
    controls = read_iso_advector_controls(name)
    scheme = reconstructionSchemeNeoN.select(controls.reconstruction_scheme)
    ops = NeoNCellCutOps(
        runtime,
        tol=controls.iso_face_tol,
        plane_search=controls.plane_search,
        surf_cell_tol=controls.surf_cell_tol,
    )
    print(f"reconstructionScheme {controls.reconstruction_scheme}, executor {executor}")
    times = {str(t): t for t in pyf.selectTimes(foam_time, ["reconstructInterface"])}
    n_samples = sum(1 for t in times if float(t) > 0)
    errors = ReconstructionError()
    wall = 0.0
    for i, centre in enumerate(sample_centres(case, n_samples), start=1):
        foam_time.setTime(times[str(i)], i)
        alpha = nfb.read_scalar_volume_field(runtime, name)
        if i == 1:
            scheme.reconstruct(ops, alpha)  # warm-up: builds the mesh stencils
        start = time.perf_counter()
        result: Any = scheme.reconstruct(ops, alpha)
        normal = np.asarray(result.normal.copy_to_host()).copy()
        cell_centre = np.asarray(result.centre.copy_to_host()).copy()
        wall += time.perf_counter() - start
        errors.add(*sample_errors(sample_shape(case, centre), cell_centre, normal))
        print(f"sample {i} centre {centre}", flush=True)
    mesh = pyf.fvMesh(foam_time)
    cell_centres = np.asarray(mesh.C().internalField()).copy()
    cell_volumes = np.asarray(mesh.V()).copy()
    delta_t: Any = FoamFile(case / "system" / "controlDict")["deltaT"]
    k1 = wall / len(errors.normal_means)
    write_error_dat(case, errors, k1, float(delta_t), cell_centres, cell_volumes)
    write_timing_dat(case, float(delta_t), time.perf_counter() - start_run)
    print("End", flush=True)


if __name__ == "__main__":
    run(sys.argv)
