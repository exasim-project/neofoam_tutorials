"""``neofoam solver incompressibleVoFNeoNSweep``: NeoFOAM's incompressibleVoFNeoN in a sweep.

The same solver (its spec, configs and ``run``); only ``--no-preprocess``, which NeoFOAM's
sweep ``solve`` rule passes, is dropped from the argv: incompressibleVoFNeoN hands its
argv to ``Foam::argList``, which rejects the option (``Invalid option: --no-preprocess``),
and it runs no preprocess tools itself (the sweep's ``setup`` rule has run them).

A ``neofoam.solvers`` entry point (pyproject): this module exports the
``incompressibleVoFNeoNSweep`` spec, NeoFOAM's ``incompressibleVoFNeoN`` object, and
``run(argv)``.
"""

from __future__ import annotations

from neofoam.solver.incompressibleVoFNeoN.incompressibleVoFNeoN import incompressibleVoFNeoN
from neofoam.solver.incompressibleVoFNeoN.incompressibleVoFNeoN import run as _run

incompressibleVoFNeoNSweep = incompressibleVoFNeoN


def run(argv: list[str]) -> None:
    _run([arg for arg in argv if arg != "--no-preprocess"])
