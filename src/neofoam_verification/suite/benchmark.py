"""A verification benchmark as data: ``benchmarks/<category>/<name>/benchmark.py``.

Each folder holds a template case (``case/``, its swept parameters in
``system/simulationParameters``), the verified reference tables (``reference/``) and a
``benchmark.py`` defining ``BENCHMARK = Benchmark(...)``::

    BENCHMARK = Benchmark(
        case=HERE / "case",
        solver="reconstructInterface",
        sweep=Sweep(
            resolutions=(8, 16, 32), smoke=(8, 16), methods=("gradAlpha",),
            parameters=lambda n, method: {"nx": n, "nz": n, "reconScheme": method},
        ),
        prepare=(Step("blockMesh"), Step("setAlphaField", "setAlphaField -dict system/x")),
        backends=("twophaseflow", "neofoam"),
        table=FunctionObjectTable("postProcessing/x/0/error.dat", ("LNormalInf", ...)),
        checks=(Published(...), AgainstBackend("twophaseflow", ...), Order(...)),
    )

The definition only says *what* runs; :mod:`.workflow` turns it into a Snakemake
workflow (one case per method and resolution and backend) and :mod:`.checks` judges
the resulting tables.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ..foam import read_function_object_dat

if TYPE_CHECKING:
    from .checks import Check
    from .plots import Plot

#: ``benchmarks/`` of this repository: a benchmark's name is its folder relative to it.
BENCHMARKS = Path(__file__).resolve().parents[3] / "benchmarks"

#: A value of ``system/simulationParameters``.
Parameter = int | float | str
#: One row of a results table: the table's columns plus ``wall_s``.
Row = dict[str, float]


@dataclass(frozen=True)
class Sweep:
    """The methods x resolutions a benchmark runs.

    ``parameters(resolution, method)`` gives the ``system/simulationParameters`` entries
    of one case; ``smoke`` are the resolutions of a quick run. ``methods`` is what runs
    by default; any other name (a newly registered model) runs with ``--method NAME``.
    """

    resolutions: tuple[int, ...]
    smoke: tuple[int, ...]
    methods: tuple[str, ...]
    parameters: Callable[[int, str], Mapping[str, Parameter]]


@dataclass(frozen=True)
class Step:
    """A case-preparation step (``blockMesh``, ``setAlphaField``) under the backend's OpenFOAM.

    ``commands`` is a shell command run in the case, or a function of the case
    directory that writes what it needs and returns the commands. ``backends``
    restricts the step to some backends (empty: all).
    """

    name: str
    commands: str | Callable[[Path], Sequence[str]] = ""
    backends: tuple[str, ...] = ()

    def commands_for(self, case: Path) -> list[str]:
        if callable(self.commands):
            return list(self.commands(case))
        return [self.commands or self.name]

    def applies_to(self, backend: str) -> bool:
        return not self.backends or backend in self.backends


@dataclass(frozen=True)
class FunctionObjectTable:
    """The result of a case: the last row of a function object's ``.dat`` (after ``Time``)."""

    path: str
    columns: tuple[str, ...]
    #: the columns that are timings: not stored in, nor compared with, reference tables
    timing: tuple[str, ...] = ()

    @property
    def stored_columns(self) -> tuple[str, ...]:
        return tuple(c for c in self.columns if c not in self.timing)

    def read(self, case: Path) -> Row:
        row = read_function_object_dat(case / self.path)[-1]
        if len(row) != len(self.columns) + 1:
            raise ValueError(f"{case / self.path}: {len(row)} columns, expected Time + columns")
        return dict(zip(self.columns, (float(v) for v in row[1:])))


@dataclass(frozen=True)
class Benchmark:
    """A template case swept over methods and resolutions, run by named backends."""

    case: Path
    solver: str
    sweep: Sweep
    backends: tuple[str, ...]
    table: FunctionObjectTable
    prepare: tuple[Step, ...] = ()
    checks: tuple[Check, ...] = ()
    #: the columns of the error table in the report (default: all of ``table``)
    report_columns: tuple[str, ...] = ()
    #: the column of ``table`` holding the mesh spacing (the report's observed orders)
    spacing: str = "length"
    #: the result columns of ``results.csv`` after backend, executor, method, n (``table``'s
    #: columns and ``wall_s``, the solver's wall time; default: all of them)
    results_columns: tuple[str, ...] = ()
    plots: tuple[Plot, ...] = ()
    #: the backend drawn dashed in the plots
    reference_backend: str = ""
    folder: Path = field(default=Path(), compare=False)

    @property
    def name(self) -> str:
        """``<category>/<name>``: the folder relative to ``benchmarks/``."""
        try:
            return self.folder.resolve().relative_to(BENCHMARKS).as_posix()
        except ValueError:
            return self.folder.name

    @property
    def reference(self) -> Path:
        return self.folder / "reference"


@dataclass(frozen=True)
class Case:
    """One case of a sweep: its name (``<method>_n<resolution>``) and parameters."""

    method: str
    resolution: int
    parameters: dict[str, Parameter]

    @property
    def name(self) -> str:
        return f"{self.method}_n{self.resolution}"


def cases(benchmark: Benchmark, methods: Sequence[str] = (), smoke: bool = False) -> list[Case]:
    """The cases of one run: ``methods`` (default the sweep's) x resolutions (or smoke)."""
    sweep = benchmark.sweep
    resolutions = sweep.smoke if smoke else sweep.resolutions
    return [
        Case(method, n, dict(sweep.parameters(n, method)))
        for method in (methods or sweep.methods)
        for n in resolutions
    ]


def load(path: Path) -> Benchmark:
    """``BENCHMARK`` of a ``benchmark.py``, with its folder filled in."""
    spec = importlib.util.spec_from_file_location(f"benchmark_{abs(hash(path))}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    benchmark = getattr(module, "BENCHMARK", None)
    if not isinstance(benchmark, Benchmark):
        raise TypeError(f"{path} defines no BENCHMARK = Benchmark(...)")
    object.__setattr__(benchmark, "folder", path.resolve().parent)
    return benchmark


def discover(folder: Path) -> list[Path]:
    """Every ``benchmark.py`` under ``folder`` (or ``folder`` itself if it is one), sorted."""
    if folder.is_file():
        return [folder]
    return sorted(folder.rglob("benchmark.py"))
