surfaceTension/staticDrop
=========================

A static drop: the parasitic currents of the Brackbill continuum surface force (CSF)
with gradAlpha curvature, in NeoFOAM's full two-phase solver ``incompressibleVoFNeoN``.
The case is NeoFOAM's ``test/solver/incompressibleVoFNeoN/cases/stationaryDroplet``;
native interFoam on the same case is the reference.

Setup
-----

.. figure:: /_static/setup/staticDrop.png
   :alt: Sketch: a 2 mm water drop in the centre of an 8 mm box, walls on three sides, open top

   An 8 mm box (x-y, one cell in z) with a water cylinder of R = 2 mm at the centre,
   no-slip walls and an open top, on the coarsest grid (n = 20).

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - 8 × 8 mm (x-y), 1 cell in z
     - ``system/blockMeshDict`` (``scale 0.001``)
   * - Drop radius R, centre
     - 2 mm, (4, 4) mm
     - ``system/setAlphaFieldDict``
   * - Surface tension σ
     - 0.07 N/m
     - ``constant/transportProperties`` ``sigma``
   * - Water ρ, ν
     - 1000 kg/m³, 1e-6 m²/s
     - ``constant/transportProperties``
   * - Air ρ, ν
     - 1 kg/m³, 1.48e-5 m²/s
     - ``constant/transportProperties``
   * - Gravity g
     - 0
     - ``constant/g``
   * - Alpha advection
     - MULES (``MULESCorr yes``, ``nAlphaCorr 2``)
     - ``system/fvSolution`` (solver default scheme)
   * - Surface force
     - CSF, gradAlpha curvature
     - ``incompressibleVoFNeoN``
   * - Time step, end time
     - ``deltaT`` 2e-5 s fixed, 4e-3 s (200 steps)
     - ``system/controlDict``
   * - Samples
     - every 10th step
     - ``controlDict`` ``writeInterval``; ``postProcess.yaml`` (``stepper``)

The drop should stay at rest, so every velocity is a spurious current, and the
pressure jump should equal σ/R = 35 Pa. The solver evaluates the metrics in-run as
NeoFOAM ``postProcess`` tables at the field write times; ``metrics.py`` derives the
rest when they are collected.

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/surfaceTension/staticDrop/``)
     - Content
   * - ``case/``
     - base case (mesh, drop, phases, σ, schemes)
   * - ``case/system/postProcess.yaml``
     - the in-situ tables: ``maxU``, ``magU_integral``, ``volume``, ``p_inside``,
       ``p_outside``, ``water``, at every written time
   * - ``metrics.py``
     - ``derive``: the derived metrics below, from the tables
   * - ``reference/interfoam.csv``
     - interFoam's jump and max\|U\| at n40, its jump deficit at n80

Metrics
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``maxU``, ``meanU``
     - spurious current [m/s]
     - max and volume-weighted mean of cell \|U\| (``mag | max``; ``mag | volIntegrate``
       over ``area | sum``)
   * - ``maxU_max``
     - largest spurious current over time
     - max over written times of ``maxU``
   * - ``Ca``, ``Ca_max``
     - capillary number
     - ``mu_water |U|max / σ``
   * - ``dp``
     - Laplace pressure jump [Pa]
     - ``mean p_rgh(r < R/2) − mean p_rgh(r > 3R/2)`` (``sphere`` and ``not sphere`` of
       radius R/2, 3R/2 about the axis on the mid-plane, ``mean``; R = 2 mm selects the
       same cells as R of the water volume)
   * - ``sigma_R``
     - exact jump [Pa]
     - σ/R, with R from the water volume (``alpha1 | volIntegrate``)
   * - ``dp_err``
     - relative jump error
     - ``|dp / sigma_R − 1|``

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/surfaceTension/staticDrop --smoke
   pixi run benchmark benchmarks/surfaceTension/staticDrop -c 1

Changed parameters
------------------

.. include:: /_generated/surfaceTension/staticDrop/params.rst

The full sweep takes about 1 min with ``-c 1``.

Larger meshes
~~~~~~~~~~~~~

``deltaT`` 2e-5 is 0.57 of the capillary limit ``sqrt(rho_avg dx³ / (2π σ))`` at n80,
so a finer mesh needs a smaller time step too: add
``n160: {block_mesh_dict_config: {blocks: [{cells: [160, 160, 1]}]}}`` and a dimension
``control_dict_config: {dt2e-5: {deltaT: 2.0e-5}, dt5e-6: {deltaT: 5.0e-6}}``. A new
dimension adds its own check groups; narrow them with ``where``.

Results
-------

.. include:: /_generated/surfaceTension/staticDrop/plots.rst

.. include:: /_generated/surfaceTension/staticDrop/key_results.rst

- **interFoam parity at n40**: Δp = 29.90 Pa against interFoam's 29.9009, max\|U\| at
  the end time 0.199 m/s.
- **Curvature converges slowly**: Δp misses σ/R by 18 %, 14.7 % and 9.6 % at R/dx = 5,
  10 and 20 (gradAlpha curvature; interFoam has the same deficit).
- **Spurious current grows with resolution** at fixed ``deltaT``: max\|U\| over time
  0.15, 0.26, 0.42 m/s (Ca up to 6.1e-3), a known CSF property.
- **Executors**: CPU and GPU agree with Serial to 1e-10.

Checks
~~~~~~

.. include:: /_generated/surfaceTension/staticDrop/verdicts.rst

A smoke run (n20 only) skips the ``reference`` checks: interFoam is stored for n40 and
n80.
