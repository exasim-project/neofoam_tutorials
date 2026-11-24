singlePhase/cavity
==================

The lid-driven cavity at Re = 100, run to the steady state with NeoFOAM's
``incompressibleFluidNeoN`` (PISO), and its centreline velocities compared with the
benchmark solution of Ghia, Ghia & Shin (1982).

Setup
-----

.. figure:: /_static/setup/cavity.png
   :alt: Sketch: the unit square, the lid moving to the right at 1 m/s, no-slip walls, the two centrelines dashed

   The unit square (x-y, one cell in z) with the lid moving at U = 1 m/s; the dashed
   centrelines are where the velocity is compared with Ghia et al.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - unit square, L = 1 m
     - ``system/blockMeshDict`` (``scale 1``)
   * - Lid velocity
     - U = (1, 0, 0) m/s
     - ``0/U`` ``movingWall``
   * - Other walls
     - no slip; p zeroGradient, reference cell 0
     - ``0/U``, ``0/p``, ``system/fvSolution``
   * - Viscosity ν
     - 0.01 m²/s, so Re = U L / ν = 100
     - ``constant/transportProperties``
   * - Flow model
     - laminar
     - ``constant/turbulenceProperties``
   * - Pressure–velocity
     - PISO, momentum predictor, 2 correctors
     - ``system/fvSolution`` ``PISO``
   * - Schemes
     - Euler, Gauss linear (second order in space)
     - ``system/fvSchemes``
   * - Linear solvers
     - CG (p), BiCGStab (U), Jacobi, tolerance 1e-8
     - ``system/fvSolution``
   * - Time step, end time
     - adaptive, ``maxCo`` 0.5; 20 s (steady state)
     - ``system/controlDict``

The case is OpenFOAM's icoFoam ``cavity`` on the unit square (OpenFOAM's tutorial uses a
0.1 m square, i.e. Re = 10), as NeoFOAM's ``neoIcoFoam/cavity`` tutorial. ``orthogonal``
corrections are written ``uncorrected`` for NeoN, which is the same on this mesh. The
solver runs through ``incompressibleFluidNeoNSweep``, a wrapper that only drops the
sweep's ``--no-preprocess`` option, which ``incompressibleFluidNeoN`` rejects.

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/singlePhase/cavity/``)
     - Content
   * - ``case/``
     - base case (mesh, lid, ν, PISO, schemes)
   * - ``case/system/postProcess.yaml``
     - the in-situ tables at every written time (every 2 s): ``u_vertical`` and
       ``v_horizontal`` (``box | rows``: U of the cells next to the centrelines),
       ``maxU`` (``mag | max``), ``dU`` (this repository's ``change`` node, ``max``)
   * - ``metrics.py``
     - the centreline errors from the ``rows`` tables and the run's cost from
       ``log.solver``; the final profiles for the plot
   * - ``reference/ghia1982.csv``
     - Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, 387–411, Table I (u on the
       vertical centreline) and Table II (v on the horizontal centreline), Re = 100
   * - ``reference/icofoam.csv``
     - OpenFOAM-v2406 ``icoFoam`` on the same case and meshes (fixed dt 0.001), evaluated
       by the same ``metrics.py`` (the tables written from its fields)

Metrics
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``u_L2``, ``u_Linf``
     - error of u on the vertical centreline x = 0.5 [m/s]
     - RMS and max of ``u − u_Ghia`` at Ghia's 15 interior points
   * - ``v_L2``, ``v_Linf``
     - error of v on the horizontal centreline y = 0.5 [m/s]
     - RMS and max of ``v − v_Ghia`` at Ghia's 15 interior points
   * - ``dU``
     - distance to the steady state [m/s]
     - max over cells of ``|U(20) − U(18)|``
   * - ``maxU``
     - largest velocity in the cells [m/s]
     - max over cells of \|U\|
   * - ``h``
     - cell size [m]
     - 1 / cells per side
   * - ``steps``, ``wall_s``, ``time_per_step_s``
     - cost of the run
     - time steps, wall time (``ClockTime``, whole seconds), wall time / steps

The centreline values are interpolated linearly between the two cell columns (rows)
next to the line, then linearly along it through the cell centres and the wall values.
NeoN has no line sampling, so the cells next to the lines come from a ``box`` of
half-width 0.03 about each line (it holds the two neighbours up to n = 160) and the
``rows`` node, which writes them every 2 s; the profile is the same as from all cells.

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/singlePhase/cavity --smoke
   pixi run benchmark benchmarks/singlePhase/cavity

Changed parameters
------------------

.. include:: /_generated/singlePhase/cavity/params.rst

The full sweep takes about 7 min with ``-c 1`` (n80: 3 min Serial, 2.5 min CPU, 1.7 min
GPU).

Larger meshes
~~~~~~~~~~~~~

Add ``n160: {block_mesh_dict_config: {blocks: [{cells: [160, 160, 1]}]}}`` to ``mesh``.
Expect the error against Ghia to level off: Ghia's own solution (129 × 129, second
order) is no more accurate than that.

Results
-------

.. include:: /_generated/singlePhase/cavity/plots.rst

.. include:: /_generated/singlePhase/cavity/key_results.rst

- **Matches Ghia on every mesh**: the centreline errors are at most 1.4e-2 (n20) and
  2e-3 to 9e-3 on n40 and n80, against velocities of order 1.
- **NeoN is OpenFOAM**: icoFoam on the same case gives the same errors (1.5 % apart on
  n80; up to 19 % on n20 and n40, where the two solvers' time steps differ and the PISO
  steady state depends weakly on it).
- **The error against Ghia stops falling at n40**: u converges at order 2.9 from n20 to
  n40, then rises at n80, and v levels off at 4.5e-3 — for icoFoam too, so this is the
  limit of the comparison (Ghia's own 129 × 129 solution), not of NeoN.
- **Executors**: CPU and GPU agree with Serial to 6e-8. On these small meshes the GPU is
  slower than Serial up to n40 and 1.7× faster on n80; CPU (4 threads) at most 1.25×.

Changes since the previous snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /_generated/singlePhase/cavity/changes.rst
