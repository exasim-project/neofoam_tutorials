surfaceTension/staticDrop
=========================

A static drop: the parasitic currents of the Brackbill continuum surface force (CSF)
with gradAlpha curvature, in NeoFOAM's full two-phase solver
``incompressibleVoFNeoN``. The case is NeoFOAM's own
``test/solver/incompressibleVoFNeoN/cases/stationaryDroplet``, and native interFoam on
the same case is the reference. Neither numufoam nor TwoPhaseFlow has a static drop
driven by surface tension.

Setup
-----

- A water cylinder of radius 2 mm (``setAlphaField``) in air, at the centre of an
  8 mm box with an open top.
- σ = 0.07 N/m, g = 0. Water: ρ = 1000, ν = 1e-6. Air: ρ = 1, ν = 1.48e-5.
- MULES (``MULESCorr yes``, ``nAlphaCorr 2``), CSF with gradAlpha curvature.
- ``deltaT 2e-5`` to t = 4e-3 (200 steps), written every 10th step.
- Solver: ``incompressibleVoFNeoNSweep`` (NeoFOAM's ``incompressibleVoFNeoN``). It
  writes no tables, so ``metrics.py`` evaluates the written fields of each case, and
  the inner time directories are pruned after that.

Inputs
~~~~~~

``benchmarks/surfaceTension/staticDrop/``:

- ``case/system/setAlphaFieldDict``: the cylinder
- ``case/constant/transportProperties``: phases and σ
- ``case/constant/g``
- ``case/system/{controlDict,fvSchemes,fvSolution}``
- ``metrics.py``: the metrics below, evaluated at every written time
- ``reference/interfoam.csv``: interFoam's jump and max\|U\| at n40, and its jump
  deficit at n80

Metrics
~~~~~~~

``maxU``, ``meanU``
   The largest and the volume-weighted mean cell \|U\|. Since the drop should be at
   rest, all of this is spurious current. ``maxU_max`` is the largest ``maxU`` over the
   written times.
``Ca``, ``Ca_max``
   Capillary numbers ``mu_water |U|max / sigma``.
``dp``
   The Laplace pressure jump ``mean p_rgh(r < R/2) - mean p_rgh(r > 3R/2)``.
``sigma_R``, ``dp_err``
   σ/R, with R taken from the water volume, and ``|dp / sigma_R - 1|``. These are
   measured as in NeoFOAM's ``test_stationaryDroplet_surface_tension``.

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/surfaceTension/staticDrop --smoke
   pixi run benchmark benchmarks/surfaceTension/staticDrop -c 1

Changed parameters
------------------

The sweep in ``benchmark.yaml``: ``mesh`` n20, n40, n80 (R/dx = 5, 10, 20) × 3 executors = 9 cases, about 1 min with ``-c 1``. Smoke: n20 ``Serial``.

.. list-table::
   :header-rows: 1
   :widths: 22 30 33 15

   * - Dimension
     - Variants
     - Sets (first variant)
     - Smoke
   * - ``mesh``
     - ``n20``, ``n40``, ``n80``
     - ``{block_mesh_dict_config: {blocks: [{cells: [20, 20, 1]}]}}``
     - ``n20``
   * - ``neo_n_control_config``
     - ``Serial``, ``CPU``, ``GPU``
     - ``{executor: Serial}``
     - ``Serial``

Larger meshes
~~~~~~~~~~~~~

``deltaT 2e-5`` is 0.57 of the capillary time-step limit
``sqrt(rho_avg dx^3 / (2 pi sigma))`` at n80. A finer mesh therefore needs a smaller
time step as well. Add the mesh, and the time step as a further dimension:

.. code-block:: yaml

   mesh:
     ...
     n160: {block_mesh_dict_config: {blocks: [{cells: [160, 160, 1]}]}}
   control_dict_config:
     dt2e-5: {deltaT: 2.0e-5}
     dt5e-6: {deltaT: 5.0e-6}

A new dimension adds a group column, and therefore its own check results. To run only
the new combination, run it as a separate benchmark, or narrow the checks with
``where``.

Results
-------

``maxU`` and ``meanU`` show the spurious current over time per mesh and executor.
``pressure_jump`` shows the end time's jump per mesh against σ/R, with interFoam's
value.

.. include:: /_generated/surfaceTension/staticDrop/plots.rst

.. include:: /_generated/surfaceTension/staticDrop/results.rst

What the full sweep shows:

- **interFoam parity at n40.** The jump is 29.9007 Pa against interFoam's 29.9009
  (14.7 % below σ/R). The end time's max\|U\| is 0.19897 m/s against 0.19927.
- **Curvature accuracy.** The jump misses σ/R by 18 %, 14.7 % and 9.6 % at
  R/dx = 5, 10 and 20; the 9.6 % at n80 is interFoam's. gradAlpha's curvature
  converges slowly.
- **Parasitic currents.** max\|U\| over time is 0.15, 0.26 and 0.42 m/s
  (Ca 2.2e-3, 3.7e-3, 6.1e-3). With CSF at a fixed time step, the current grows with
  resolution.
- **Executors.** Serial, CPU and GPU agree to 1e-10.

Checks
~~~~~~

.. include:: /_generated/surfaceTension/staticDrop/checks.rst

Per executor:

- ``reference interfoam.csv``: ``dp`` to 1e-4, ``maxU`` to 1.5e-2, ``dp_err`` to
  1e-2. These are the NeoFOAM test's tolerances; the linear solvers stop at different
  iterates. Only n40 (and n80 for ``dp_err``) are stored, so a smoke run on n20
  skips them.
- ``maximum dp_err`` ≤ 0.2: the jump within 20 % of σ/R.
- ``maximum maxU_max`` ≤ 0.5 m/s, a regression bound on the spurious current.
- ``agreement executor`` to 1e-8: CPU and GPU against Serial. It is skipped when only
  one executor ran.
