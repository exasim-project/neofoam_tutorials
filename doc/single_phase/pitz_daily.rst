singlePhase/pitzDaily
=====================

The turbulent flow over a backward-facing step (Pitz & Daily 1983) with k-ε, solved to
the steady state with NeoFOAM's ``incompressibleFluidNeoN`` (SIMPLE), and compared with
OpenFOAM-v2406 ``simpleFoam`` on the same case and meshes.

Setup
-----

.. figure:: /_static/setup/pitzDaily.png
   :alt: Sketch: the inlet channel, the step of height h on the lower wall, the channel tapering to the outlet, the profile stations at x/h = 1, 3, 5, 7

   OpenFOAM's ``pitzDaily`` geometry (x-y, one cell in z): inlet at the left, the step
   of height h = 25.4 mm at x = 0, the outlet at the right; the dashed lines are the
   profile stations.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - OpenFOAM's pitzDaily, step height h = 25.4 mm
     - ``system/blockMeshDict`` (5 blocks, ``scale 0.001``)
   * - Inlet
     - U = (10, 0, 0) m/s, k = 0.375 m²/s², ε = 14.855 m²/s³
     - ``0/U``, ``0/k``, ``0/epsilon``
   * - Outlet
     - p = 0, zero gradient for U, k, ε
     - ``0/*``
   * - Walls
     - no slip, k-ε wall functions
     - ``0/U``, ``0/k``, ``0/epsilon``, ``0/nut``
   * - Viscosity ν
     - 1e-5 m²/s, so Re_h = U h / ν = 25 400
     - ``constant/transportProperties``
   * - Turbulence
     - RAS ``kEpsilon`` (NeoN's native closure)
     - ``constant/turbulenceProperties``
   * - Pressure–velocity
     - SIMPLE (``consistent no``), relaxation p 0.3, U, k, ε 0.7
     - ``system/fvSolution``
   * - Schemes
     - bounded linearUpwind (U), limitedLinear (k, ε), Gauss linear corrected
     - ``system/fvSchemes``
   * - Iterations
     - 1500, fields written every 500
     - ``system/controlDict``

The case is NeoFOAM's ``pitzDaily_steady`` tutorial: OpenFOAM's ``simpleFoam`` tutorial
with plain SIMPLE and explicit pressure relaxation (the upstream tutorial is SIMPLEC with
0.9 relaxation). NeoN has no ``residualControl``, so every case runs all 1500 iterations
and the metrics report the iteration where the tutorial's tolerances are first met. NeoN
maps the linear solvers to Ginkgo (GAMG → multigrid-preconditioned CG, smoothSolver →
BiCGStab). The solver runs through ``incompressibleFluidNeoNSweep`` (see
:doc:`cavity`).

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/singlePhase/pitzDaily/``)
     - Content
   * - ``case/``
     - base case (mesh, fields, k-ε, SIMPLE, schemes)
   * - ``metrics.py``
     - the metrics below, per iteration from ``log.solver`` and at the written fields
   * - ``reference/openfoam.csv``, ``reference/openfoam_profiles.csv``
     - OpenFOAM-v2406 ``simpleFoam`` on the same case and meshes, 1500 iterations,
       evaluated by the same ``metrics.py``
   * - ``reference/pitz_daily_1983.csv``
     - the measured reattachment length x_r / h ≈ 7.0 (Pitz & Daily 1983, AIAA J. 21,
       1565–1570; as commonly quoted for this case)
   * - ``openfoam_reference.py``
     - reruns OpenFOAM and rewrites ``reference/openfoam*.csv`` (below)

The OpenFOAM reference is rebuilt with (``$OPENFOAM_BASHRC``, default
``~/OpenFOAM/OpenFOAM-v2406/etc/bashrc``, is sourced for the runs; about 30 s):

.. code-block:: bash

   pixi run python benchmarks/singlePhase/pitzDaily/openfoam_reference.py runs/pitzDaily

Metrics
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``x_r_h``
     - reattachment length over the step height
     - most downstream x where Ux of the lower-wall cells (y = −h, x > 0) turns from
       negative to positive, linear between faces; divided by h
   * - ``Umin_xh1``, ``_xh3``, ``_xh5``
     - strongest backflow at x/h = 1, 3, 5
     - min of Ux / U_inlet on the profile at that station
   * - ``profile_err``
     - profile difference to OpenFOAM
     - max over the stations x/h = 1, 3, 5, 7 of RMS(Ux − Ux_OpenFOAM) / U_inlet, same mesh
   * - ``iterations``
     - iterations to convergence
     - first iteration with initial residuals Ux, Uy, k, ε < 1e-3 and p < 1e-2 (the
       tutorial's ``residualControl``)
   * - ``Ux_res``, ``p_res``
     - residuals at the last iteration
     - initial residuals printed by the solver
   * - ``wall_s``
     - cost of the 1500 iterations
     - last ``ClockTime`` of the log (whole seconds)

Profiles are interpolated linearly in x between the two cell columns next to the station
and in y through the cell centres and the walls' no-slip values.

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/singlePhase/pitzDaily --smoke
   pixi run benchmark benchmarks/singlePhase/pitzDaily

Changed parameters
------------------

.. include:: /_generated/singlePhase/pitzDaily/params.rst

The full sweep takes about 5 min with ``-c 1`` (tutorial mesh: 92 s Serial, 84 s CPU,
40 s GPU; OpenFOAM's serial simpleFoam takes 17 s).

Larger meshes
~~~~~~~~~~~~~

A finer mesh doubles the cells of all five blocks, e.g. ``fine`` with ``[36, 60, 1]``,
``[360, 54, 1]``, ``[360, 60, 1]``, ``[50, 54, 1]``, ``[50, 60, 1]`` (the comment in
``benchmark.yaml``). Then rerun ``openfoam_reference.py`` so the OpenFOAM tables hold the
new mesh; a mesh without stored rows is skipped by the ``reference`` checks.

Results
-------

.. include:: /_generated/singlePhase/pitzDaily/plots.rst

.. include:: /_generated/singlePhase/pitzDaily/key_results.rst

- **NeoN reproduces simpleFoam**: x_r / h = 6.97 (coarse) and 7.025 (tutorial) against
  OpenFOAM's 6.967 and 7.021, the backflow minima to 0.2 %, the profiles to 3e-4 of
  U_inlet (RMS).
- **The experiment**: x_r / h ≈ 7.0 of Pitz & Daily is matched within 0.5 %, by both
  codes alike.
- **Convergence**: the tutorial's tolerances are met after about 350 (coarse) and 850
  (tutorial) iterations, within 4 % of OpenFOAM's 356 and 866. The p residual then
  stalls at about 5e-4 (OpenFOAM: 3e-3).
- **Executors** agree with Serial to 7e-4, the level the stalled residual allows.

Checks
~~~~~~

.. include:: /_generated/singlePhase/pitzDaily/verdicts.rst
