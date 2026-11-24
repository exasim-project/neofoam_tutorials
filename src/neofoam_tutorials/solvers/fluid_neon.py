"""``neofoam solver incompressibleFluidNeoNSweep``: NeoFOAM's incompressibleFluidNeoN in a sweep.

The same solver (its spec, configs and ``run``); only ``--no-preprocess``, which NeoFOAM's
sweep ``solve`` rule passes, is dropped from the argv: incompressibleFluidNeoN hands its
argv to ``Foam::argList``, which rejects the option (``Invalid option: --no-preprocess``),
and it runs no preprocess tools itself (the sweep's ``setup`` rule has run them).

A ``neofoam.solvers`` entry point (pyproject): this module exports the
``incompressibleFluidNeoNSweep`` spec, NeoFOAM's ``incompressibleFluidNeoN`` object, and
``run(argv)``.
"""

from __future__ import annotations

from neofoam.solver.incompressibleFluidNeoN.incompressibleFluidNeoN import (
    incompressibleFluidNeoN,
)
from neofoam.solver.incompressibleFluidNeoN.incompressibleFluidNeoN import run as _run

incompressibleFluidNeoNSweep = incompressibleFluidNeoN


def run(argv: list[str]) -> None:
    _run([arg for arg in argv if arg != "--no-preprocess"])
