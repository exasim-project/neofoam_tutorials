"""Verification of NeoFOAM's MULES VoF advection against OpenFOAM.

Benchmarks are TwoPhaseFlow's advection testsuite cases (:mod:`.benchmarks`), the
metrics are TwoPhaseFlow's ``volumeFractionError`` function object transcribed to numpy
(:mod:`.metrics`, :mod:`.cut_cell`), the external reference is TwoPhaseFlow's C++
``advectorVoF`` with its MULES scheme (:mod:`.reference`), and the solver under test is
reached through one adapter, :func:`.backend.run_case`.
"""

__version__ = "0.1.0"
