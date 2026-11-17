"""``neofoam solver advectorVoF``: TwoPhaseFlow's advectorVoF on NeoFOAM.

Advects alpha in the case's prescribed velocity (``0/U``; ``phi`` from ``0/phi`` or
``fvc::flux(U)``) with the ``advectionModelNeoN`` member named by fvSolution's
``advectionScheme`` (``isoAdvector`` with the ``reconstructionScheme`` of
``solvers.alpha.water``, or ``MULES``) on the ``executor`` of ``system/controlDict``.
The solver is a subset of ``incompressibleVoFNeoN``: its runtime, solution loop,
field writer and alpha-advection member, without the pressure-velocity and
surface-force members. ``U`` and ``phi`` stay as read (no ``period`` /
``spirallingFlow`` / ``reverseTime`` modulation: steady flows only).

The time step is fixed: before the first step it is set, undamped, to
advectorVoF's setDeltaT.H target ``min(maxCo/Co, maxAlphaCo/alphaCo) deltaT``
(``adaptiveTimeStepNeoN``'s ``courant_limit``, contributed here as the
``initialTimeStepConstraint``; ``deltaT`` of controlDict is its ceiling) and snapped
onto the write interval. For a uniform velocity that is advectorVoF's step; NeoFOAM's
adaptive time step damps the growth instead (interFoam).

Writes ``volumeFractionError.dat`` (:mod:`.volume_fraction_error_io`) at the function
object's write times and ``timing.dat`` at the end.

A ``neofoam.solvers`` entry point (pyproject): this module exports the ``advectorVoF``
spec, with the configs a sweep varies (mesh, executor, time step, scheme), and
``run(argv)``.
"""

# NB: no ``from __future__ import annotations`` -- the framework injects operation and
# contribution parameters by their live annotations (Context, ControlDictConfig).

import os
import sys
import time
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from neofoam.algorithms.solution_loop.interfaces import initialTimeStepConstraint
from neofoam.framework.context import Context
from neofoam.framework.graph import DAGResolver
from neofoam.framework.initialization import (
    ConfigContext,
    Depends,
    InitializerBuilder,
    InitStep,
    LoadResult,
    StagedInitRunner,
    StagedInitSpec,
    field,
    lazy,
)
from neofoam.framework.initialization import model as init_model
from neofoam.framework.model import Model, ModelRuntime
from neofoam.framework.operations import (
    IterativeOp,
    Operation,
    Operations,
    SequentialOp,
    StepBuilder,
)
from neofoam.framework.solver import Solver
from neofoam.framework.tools import PreprocessConfig
from neofoam.framework.types import OperationMetadata
from neofoam.io import OF, BaseConfig, IOStrategy
from neofoam.solver.incompressibleVoF.configs import ControlDictConfig
from neofoam.solver.neon_runtime import NeoNControlConfig
from neofoam.tools.block_mesh import BlockMeshDictConfig
from pydantic import ConfigDict

from .volume_fraction_error_io import VolumeFractionErrorTable, write_timing_dat

ALPHA = "alpha.water"


@IOStrategy(OF("system/fvSolution"))
class AdvectionSchemeConfig(BaseConfig):  # type: ignore[misc]
    """``advectionScheme`` of ``system/fvSolution``: the ``advectionModelNeoN`` member.

    Example::

        advectionScheme isoAdvector;   // or MULES

    The other entries (``solvers`` ...) are kept: a merged payload rewrites only this key.
    """

    model_config = ConfigDict(extra="allow")

    advectionScheme: str = "MULES"


advectorVoF = Solver("advectorVoF")
for _config in (
    PreprocessConfig,
    BlockMeshDictConfig,
    NeoNControlConfig,
    ControlDictConfig,
    AdvectionSchemeConfig,
):
    advectorVoF.config(_config)

# advectorVoF's undamped time step: NeoFOAM's setDeltaT.H target as the first step's limit
# (the contribution is registered by create_init, which imports the NeoN models).
advectorVoFTimeStep = Model("advectorVoFTimeStep").labeled("Fixed time step (alpha Courant)")
advectorVoFTimeStep.config(ControlDictConfig)


def _runtime_steps(argv: list[str]) -> list[InitStep]:
    """``Foam::Time`` and the NeoN runtime with NeoN's scheme names (incompressibleVoFNeoN's)."""
    import pybFoam as pyf
    from neofoam import neofoam_bindings as nfb
    from neofoam.solver.neon_runtime import requested_executor

    def create_neon_runtime(ctx: dict[str, Any]) -> Any:
        rt = nfb.create_adapter_run_time(ctx["_foam_time"], requested_executor())
        rt.fv_schemes_dict = nfb.map_fv_schemes(rt.fv_schemes_dict)
        return rt

    return [
        lazy("_arg_list", lambda _ctx: pyf.argList(argv)),
        lazy("_foam_time", lambda ctx: pyf.Time(ctx["_arg_list"]), depends_on=["_arg_list"]),
        lazy("_neon_runtime", create_neon_runtime, depends_on=["_foam_time"]),
        init_model("neon_runtime", lambda ctx: ctx["_neon_runtime"], depends_on=["_neon_runtime"]),
    ]


def create_init() -> StagedInitRunner:
    """LOAD the advection member, loop, writer and time step; BUILD runtime, U, the member."""
    from neofoam import neofoam_bindings as nfb
    from neofoam.solver.incompressibleFluidNeoN.models.field_writer import fieldWriter
    from neofoam.solver.incompressibleFluidNeoN.models.solution_loop import (
        neon_loop_backend_steps,
        solutionLoop,
    )
    from neofoam.solver.incompressibleVoFNeoN.models.alpha_advection import advectionModelNeoN
    from neofoam.solver.incompressibleVoFNeoN.models.field_writer import (
        neon_vof_writer_backend_steps,
    )
    from neofoam.solver.incompressibleVoFNeoN.models.time_step import courant_limit

    advectorVoFTimeStep.contributes(initialTimeStepConstraint)(courant_limit)

    spec_builder = StagedInitSpec.build("advectorVoF")
    case = Path(".")

    @spec_builder.load  # type: ignore[untyped-decorator]
    def load_config() -> LoadResult:
        return LoadResult(
            core_models=[
                advectionModelNeoN.detect_and_create(),
                solutionLoop.instantiate(case, "main"),
                fieldWriter.instantiate(case, "main"),
            ],
            optional_models=[advectorVoFTimeStep.instantiate(case, advectorVoFTimeStep.name)],
        )

    @spec_builder.resolve  # type: ignore[untyped-decorator]
    def resolve_models(config: ConfigContext) -> None:
        return None

    @spec_builder.build  # type: ignore[untyped-decorator]
    def build_lazy(core_models: list[Any], optional_models: list[Any]) -> list[InitStep]:
        alpha_model, loop_model, writer_model = core_models
        builder = InitializerBuilder()
        builder.extend(_runtime_steps(runner.argv))
        builder.add_core_models(
            [("solution_loop_model", loop_model), ("field_writer_model", writer_model)]
        )
        builder.extend(neon_loop_backend_steps())
        builder.extend(neon_vof_writer_backend_steps())
        # the prescribed velocity (the pimple member reads it in incompressibleVoFNeoN)
        builder.add(
            field(
                "U",
                lambda ctx: nfb.read_vector_volume_field(ctx["_neon_runtime"], "U"),
                depends_on=["_neon_runtime"],
            )
        )
        builder.add_core_models([("alpha_advection", alpha_model)])
        builder.extend(alpha_model.build_steps())
        for optional_model in optional_models:
            builder.add_model(optional_model.name, optional_model)
        builder.add(
            init_model("solutionLoop", lambda _ctx: loop_model, depends_on=["models.solution_loop"])
        )
        steps: list[InitStep] = builder.build()
        return steps

    runner = StagedInitRunner(spec_builder.finalize())
    return runner


@advectorVoF.initializer  # type: ignore[untyped-decorator]
def initialize(self: Any, init: Annotated[StagedInitRunner, Depends(create_init)]) -> Context:
    return init.run()


class _Monitor:
    """The volumeFractionError table and the advection's wall time per step."""

    def __init__(self, ctx: Context) -> None:
        self.table = VolumeFractionErrorTable(
            Path.cwd(), _host(ctx.fields["alpha1"]), _host(ctx.fields["U"]), ctx.time.value
        )
        self.advection_s = 0.0
        self.steps = 0
        self._start = 0.0

    def tic(self, ctx: Context) -> None:
        self._start = time.perf_counter()

    def toc(self, ctx: Context) -> None:
        self.advection_s += time.perf_counter() - self._start
        self.steps += 1
        if self.table.due(ctx.time.value, ctx.time.delta_t):
            t_adv = self.advection_s / self.steps
            self.table.write(ctx.time.value, _host(ctx.fields["alpha1"]), t_adv)


def _host(volume_field: Any) -> Any:
    return np.asarray(volume_field.internal_vector().copy_to_host()).copy()


def _op(name: str, func: Any) -> Operation:
    return Operation(func=SequentialOp(func), metadata=OperationMetadata(op_name=name))


@advectorVoF.execution_graph_step  # type: ignore[untyped-decorator]
def execution_graph(self: Any, ctx: Context) -> tuple[StepBuilder, Operations]:
    """set_time_step -> increment_time -> alpha_advection -> volumeFractionError -> write."""
    from neofoam.solver.incompressibleFluidNeoN.models.solution_loop import (
        SolutionLoopPredicate,
    )

    alpha_model, loop_model, writer_model = self.state.core_models
    alpha_ops = Operations(alpha_model.build_operations_for(alpha_model))
    loop_ops = Operations(_runtime_of(loop_model).operations)
    writer_ops = Operations(_runtime_of(writer_model).operations)
    monitor = _Monitor(ctx)
    ctx.models["volume_fraction_error"] = monitor

    builder = StepBuilder()
    time_loop = Operation(
        func=IterativeOp(SolutionLoopPredicate()), metadata=OperationMetadata(op_name="time_loop")
    )
    with builder.loop(time_loop) as step:
        step.step(loop_ops["set_time_step"])
        step.step(loop_ops["increment_time"])
        step.step(_op("tic", monitor.tic))
        step.step(alpha_ops["alpha_advection"])
        step.step(_op("volume_fraction_error", monitor.toc))
        step.step(writer_ops["write_output"])
    return builder, Operations()


def _runtime_of(model: Any) -> ModelRuntime:
    assert isinstance(model, ModelRuntime)
    return model


def run(argv: list[str]) -> None:
    """Advect the case (``-case DIR``, default the working directory) to ``endTime``."""
    from neofoam.solver.neon_runtime import ensure_neon_initialized

    start = time.perf_counter()
    if "-case" in argv:
        os.chdir(argv[argv.index("-case") + 1])
    ensure_neon_initialized(["advectorVoF"])
    solver = advectorVoF.instantiate(argv=["advectorVoF"])
    ctx = solver.initialize()
    builder, model_ops = solver.execution_graph(ctx=ctx)
    DAGResolver().resolve(builder, model_ops).operations.run(ctx)
    monitor = ctx.models["volume_fraction_error"]
    write_timing_dat(Path.cwd(), ctx.time.value, time.perf_counter() - start, monitor.steps)
    print("End", flush=True)


if __name__ == "__main__":
    run(sys.argv)
