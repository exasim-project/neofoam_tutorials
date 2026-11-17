"""What a benchmark's results are verified against, and the results tables themselves.

A results table (``tables/<backend>.csv`` of a run, ``reference/<backend>.csv`` of a
benchmark) has one row per case: ``method``, ``resolution`` and the benchmark table's
columns (``wall_s`` in a run's tables). The checks:

* :class:`Published` -- a published table of the same case (numufoam's), per row;
* :class:`AgainstBackend` -- the verified reference table of a backend stored under
  ``reference/`` (for that backend itself: it still reproduces it);
* :class:`Order` -- the observed convergence order, the least-squares slope of
  ``log(error)`` over ``log(spacing)`` across the run's resolutions.

Each check returns one :class:`CheckResult` per backend and method; rows the check
has nothing to compare with are ``skip``.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import numpy as np

from .benchmark import Benchmark, Row

Status = Literal["pass", "fail", "skip"]
#: ``(method, resolution) -> {column: value}``, as :func:`read_table` and numufoam's reader.
Keyed = dict[tuple[str, int], Row]


@dataclass(frozen=True)
class Result:
    """One case's row of a results table."""

    backend: str
    method: str
    resolution: int
    values: Row


@dataclass(frozen=True)
class CheckResult:
    check: str
    backend: str
    method: str
    status: Status
    detail: str


class Check(Protocol):
    def evaluate(self, benchmark: Benchmark, results: Sequence[Result]) -> list[CheckResult]: ...


def read_table(path: Path) -> Keyed:
    with path.open(newline="") as file:
        return {
            (row.pop("method"), int(row.pop("resolution"))): {k: float(v) for k, v in row.items()}
            for row in csv.DictReader(file)
        }


def write_table(path: Path, rows: Keyed, columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["method", "resolution", *columns])
        for (method, n), row in sorted(rows.items()):
            writer.writerow([method, n, *(f"{row[c]:.17g}" for c in columns)])


def _groups(results: Iterable[Result]) -> dict[tuple[str, str], list[Result]]:
    groups: dict[tuple[str, str], list[Result]] = {}
    for result in sorted(results, key=lambda r: (r.backend, r.method, r.resolution)):
        groups.setdefault((result.backend, result.method), []).append(result)
    return groups


def _compare(
    name: str, rows: list[Result], other: Keyed, columns: Sequence[str], rtol: float
) -> CheckResult:
    backend, method = rows[0].backend, rows[0].method
    pairs = [(r, other[method, r.resolution]) for r in rows if (method, r.resolution) in other]
    if not pairs:
        return CheckResult(name, backend, method, "skip", "no stored row for these resolutions")
    worst, where = 0.0, ""
    for result, expected in pairs:
        for column in columns:
            a, b = result.values[column], expected[column]
            diff = abs(a - b) / max(abs(b), np.finfo(float).tiny)
            if diff >= worst:
                worst, where = diff, f"{column} n={result.resolution}"
    status: Status = "pass" if worst <= rtol else "fail"
    resolutions = ",".join(str(r.resolution) for r, _ in pairs)
    return CheckResult(
        name,
        backend,
        method,
        status,
        f"max rel diff {worst:.1e} ({where}), rtol {rtol:g}, n={resolutions}",
    )


@dataclass(frozen=True)
class Published:
    """A published table (``reference/<file>``, read by ``read``) to ``rtol`` per value."""

    file: str
    read: Callable[[Path], Keyed]
    columns: tuple[str, ...]
    rtol: float
    #: the backends held to it (empty: all)
    backends: tuple[str, ...] = ()

    def evaluate(self, benchmark: Benchmark, results: Sequence[Result]) -> list[CheckResult]:
        published = self.read(benchmark.reference / self.file)
        name = f"published {self.file}"
        return [
            _compare(name, rows, published, self.columns, self.rtol)
            for (backend, _), rows in _groups(results).items()
            if not self.backends or backend in self.backends
        ]


@dataclass(frozen=True)
class AgainstBackend:
    """The stored reference table of ``backend`` (``reference/<backend>.csv``) to ``rtol``."""

    backend: str
    columns: tuple[str, ...]
    rtol: float

    def evaluate(self, benchmark: Benchmark, results: Sequence[Result]) -> list[CheckResult]:
        path = benchmark.reference / f"{self.backend}.csv"
        name = f"against {self.backend}"
        groups = _groups(results)
        if not path.is_file():
            return [CheckResult(name, b, m, "skip", f"no stored {path.name}") for b, m in groups]
        stored = read_table(path)
        return [_compare(name, rows, stored, self.columns, self.rtol) for rows in groups.values()]


@dataclass(frozen=True)
class Order:
    """The fitted order of ``column`` over ``spacing`` within ``[minimum, maximum]``."""

    column: str
    minimum: float
    maximum: float = np.inf
    spacing: str = "length"
    #: the methods held to it (empty: all)
    methods: tuple[str, ...] = ()

    def evaluate(self, benchmark: Benchmark, results: Sequence[Result]) -> list[CheckResult]:
        out = []
        name = f"order {self.column}"
        for (backend, method), rows in _groups(results).items():
            if self.methods and method not in self.methods:
                continue
            if len(rows) < 2:
                out.append(CheckResult(name, backend, method, "skip", "one resolution"))
                continue
            order = fitted_order(
                [r.values[self.spacing] for r in rows], [r.values[self.column] for r in rows]
            )
            status: Status = "pass" if self.minimum <= order <= self.maximum else "fail"
            bounds = f">= {self.minimum:g}" + (
                "" if np.isinf(self.maximum) else f", <= {self.maximum:g}"
            )
            out.append(CheckResult(name, backend, method, status, f"{order:.2f} ({bounds})"))
        return out


def fitted_order(spacing: Sequence[float], error: Sequence[float]) -> float:
    """``-d log(error) / d log(1/h)``, least squares over all resolutions."""
    return float(-np.polyfit(np.log(1.0 / np.asarray(spacing)), np.log(np.asarray(error)), 1)[0])
