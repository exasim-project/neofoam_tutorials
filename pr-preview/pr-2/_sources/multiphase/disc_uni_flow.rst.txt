advection/discUniFlow
=====================

A disc translated in a uniform flow: the paper's advection test (Scheufler & Roenby,
arXiv 1801.05382, sec. 4.2.1, as in numufoam). NeoN's isoAdvector (``gradAlpha``
reconstruction) and NeoN's MULES are compared with numufoam's stored errors over
resolution and Courant number.

Setup
-----

.. figure:: /_static/setup/discUniFlow.png
   :alt: Sketch: a disc of radius 0.2 moving from (0.25, 0.25) to (0.75, 0.75) in the unit square

   The unit square (x-z, one cell in y) on the coarsest grid (n = 10). The disc starts
   at (0.25, 0.25) and ends at (0.75, 0.75) after U t.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - 1 × 1 (x-z), 1 cell in y
     - ``system/blockMeshDict``
   * - Disc radius R, start
     - 0.2, (0.25, 0.25)
     - ``system/setAlphaFieldDict``
   * - Velocity U
     - (1, 1), uniform, fixed
     - ``0/U`` ``internalField``
   * - End time
     - 0.5 (end position (0.75, 0.75))
     - ``system/controlDict`` ``endTime``
   * - Time step
     - fixed, from ``maxAlphaCo`` (``maxCo`` off)
     - ``system/controlDict``
   * - Method
     - isoAdvector (gradAlpha, ``volTaylor``) or MULES
     - ``system/fvSolution`` ``advectionScheme``
   * - MULES gradient
     - Gauss linear
     - ``system/fvSchemes`` ``gradSchemes``
   * - Solver
     - ``advectorVoF``
     - ``benchmark.yaml`` ``solver``

Only alpha is transported; the velocity stays fixed. The errors are measured once,
at t = 0.5, against the exactly cut disc at its end position.

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/advection/discUniFlow/``)
     - Content
   * - ``case/``
     - base case (mesh, disc, U, controls incl. the ``volumeFractionError`` function)
   * - ``case/system/postProcess.yaml``
     - the in-situ tables at the function's write times (every 0.1): ``Eshape``,
       ``mass``, ``mass0``, ``alpha_min``, ``alpha_max``
   * - ``metrics.py``
     - ``derive``: ``Emass`` and ``Ebound`` from the tables
   * - ``reference/numufoam.csv``
     - numufoam's ``error.csv``: isoAlpha, plicRDF, MULES at CFL 0.05 to 0.5, n10 to
       n320

Metrics
~~~~~~~

TwoPhaseFlow's ``volumeFractionError`` at t = 0.5, from NeoFOAM ``postProcess`` tables.
The solver's ``volumeFractionError.dat`` (the same errors, to round-off) supplies the
timing and mesh columns.

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``Eshape`` (E1)
     - shape error (absolute)
     - ``Σ V |alpha − alpha_exact|``, ``alpha_exact``: the initial disc moved by U t
       (this repository's ``shapeError`` source, NeoFOAM's ``cutCellIso``; ``volIntegrate``)
   * - ``Emass``
     - mass error
     - ``|Σ V alpha − initial mass|`` (``alpha1 | volIntegrate``; the start time's
       ``alpha.water``: this repository's ``startField`` source)
   * - ``Ebound``
     - boundedness error
     - ``max(−min alpha, max alpha − 1)`` (``alpha1 | min``, ``max``)
   * - ``Tadv``, ``wall_s``, ``steps``
     - timings, step count
     - wall time per advection, solver wall time, number of steps

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/advection/discUniFlow --smoke
   pixi run benchmark benchmarks/advection/discUniFlow -c 1

Changed parameters
------------------

.. include:: /_generated/advection/discUniFlow/params.rst

About 1.5 min with ``-c 1``. numufoam's CFLs 0.05 and 0.2 are commented-out variants
too.

Larger meshes
~~~~~~~~~~~~~

Uncomment ``n80``, ``n160``, ``n320`` in ``benchmark.yaml``. n320 needs about 20 MB per
case and 1–4 min on ``Serial`` per CFL. Neither method converges on n10 to n40; on
n320, MULES reaches 3.5 × numufoam's E1.

Results
-------

.. include:: /_generated/advection/discUniFlow/plots.rst

.. include:: /_generated/advection/discUniFlow/key_results.rst

- **Mass and bounds**: mass is conserved to round-off for both methods. isoAdvector
  stays in [0, 1]; MULES does only at CFL 0.1 (bound error 1.5e-2 at CFL 0.5).
- **MULES vs numufoam**: E1 is 0.84–0.92 × numufoam's at n10 and n20 (CFL 0.1) and
  1.67 × at n40; NeoN uses a Gauss linear interface normal, numufoam
  ``pointCellsLeastSquares``.
- **isoAdvector with gradAlpha does not converge** on this sharp disc: E1 = 6.9e-3,
  7.4e-3, 8.4e-3 on n10 to n40 at CFL 0.1. OpenFOAM's gradAlpha behaves the same
  (see :doc:`disc_uni_flow_testsuite` for exact parity); plicRDF and isoAlpha are not
  yet in NeoN.

The alpha fields at t = 0.5 on n40 show the difference:

.. figure:: /_static/discuniflow/isoAdvector_n40_neofoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, NeoFOAM isoAdvector gradAlpha, n40

   NeoFOAM, isoAdvector with gradAlpha, n40, maxAlphaCo 0.1: E1 = 8.4e-3. The error
   (right) reaches ±0.5 in cells along the whole interface.

.. figure:: /_static/discuniflow/plicRDF_n40_openfoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, OpenFOAM isoAdvector plicRDF, n40

   OpenFOAM-v2506, isoAdvector with plicRDF, same case: E1 = 7.7e-4, with errors below
   ±0.06. This is the reconstruction NeoN still needs.

Changes since the previous snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /_generated/advection/discUniFlow/changes.rst
