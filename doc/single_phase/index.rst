Single phase
============

These benchmarks verify NeoFOAM's single-phase incompressible solver
``incompressibleFluidNeoN`` on NeoN: a laminar transient case run to the steady state
(PISO) and a turbulent steady case (SIMPLE, k-ε). Each page says what is tested
and why, describes the case and the parameter changes, and shows and explains the
results.

- :doc:`cavity`: laminar lid-driven cavity at Re = 100, PISO to the steady state.
- :doc:`pitz_daily`: turbulent backward-facing step, k-ε, SIMPLE (OpenFOAM's pitzDaily).

.. toctree::
   :maxdepth: 1

   cavity
   pitz_daily
