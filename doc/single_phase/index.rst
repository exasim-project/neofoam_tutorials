Single phase
============

These benchmarks verify NeoFOAM's single-phase incompressible solver
``incompressibleFluidNeoN`` on NeoN: a laminar transient case run to the steady state
(PISO) and a turbulent steady case (SIMPLE, k-ε). Each page describes the setup, the
metrics, the current results and the checks.

.. list-table::
   :header-rows: 1
   :widths: 14 14 30 30 12

   * - Benchmark
     - Physics
     - What NeoFOAM shows
     - Status / limit
     - Serial / CPU / GPU
   * - :doc:`cavity`
     - Laminar lid-driven cavity, Re = 100, PISO to the steady state
     - Centreline velocities within 1.4e-2 of Ghia et al. (1982) on n20 and 2e-3 to
       9e-3 on n40, n80; the same errors as OpenFOAM's ``icoFoam`` (1.5 % apart on n80).
     - The error against Ghia stops falling beyond n40, for icoFoam too: the limit of
       the reference.
     - agree to 6e-8
   * - :doc:`pitz_daily`
     - Turbulent backward-facing step, k-ε, SIMPLE (OpenFOAM's pitzDaily)
     - Reattachment length x_r / h = 7.025 against ``simpleFoam``'s 7.021 on the same
       mesh; profiles within 3e-4 of U_inlet; the measured ≈ 7.0 within 0.5 %.
     - No ``residualControl`` in NeoN: 1500 iterations are always run (converged after
       about 850).
     - agree to 7e-4

.. toctree::
   :maxdepth: 1

   cavity
   pitz_daily
