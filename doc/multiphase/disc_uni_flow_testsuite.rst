advection/discUniFlowTestsuite
==============================

TwoPhaseFlow's testsuite variant of the disc in uniform flow
(``testsuite/advection/test-discUniFlow``): a long run (t = 4, 1200 steps) on one mesh,
compared with stored runs of TwoPhaseFlow's ``advectorVoF`` with the same schemes. This
is the parity test: NeoFOAM has to reproduce the C++ reference.

Setup
-----

.. figure:: /_static/setup/discUniFlowTestsuite.png
   :alt: Sketch: a disc of radius 0.25 moving from (0.5, 0.5) to (4.5, 2.5) in a 5 x 3 domain

   The 5 × 3 domain (x-z, one cell in y) with its 100 × 60 grid. The disc moves from
   (0.5, 0.5) to (4.5, 2.5).

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain, mesh
     - 5 × 3 (x-z), 100 × 60 cells (dx = 0.05)
     - ``system/blockMeshDict``
   * - Disc radius R, start
     - 0.25, (0.5, 0.5)
     - ``system/setAlphaFieldDict``
   * - Velocity U
     - (1, 0.5), uniform, fixed
     - ``0/U`` ``internalField``
   * - End time
     - 4 (end position (4.5, 2.5))
     - ``system/controlDict`` ``endTime``
   * - Time step
     - ``maxAlphaCo`` 0.1 → dt = 1/300, 1200 steps
     - ``system/controlDict``
   * - Method
     - isoAdvector (gradAlpha) or MULES
     - ``system/fvSolution`` ``advectionScheme``
   * - MULES gradient
     - Gauss linear
     - ``system/fvSchemes`` ``gradSchemes``

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/advection/discUniFlowTestsuite/``)
     - Content
   * - ``case/``
     - base case (mesh, disc, U, controls, schemes)
   * - ``case/system/postProcess.yaml``, ``metrics.py``
     - the in-situ tables (every 1 s) and the derived ``Emass``, ``Ebound``, as in
       :doc:`disc_uni_flow`
   * - ``reference/twophaseflow_mules.csv``
     - TwoPhaseFlow ``advectorVoF`` with ``MULESScheme`` (OpenFOAM-v2506)
   * - ``reference/twophaseflow_isoadvection.csv``
     - TwoPhaseFlow ``advectorVoF`` with isoAdvection and gradAlpha

Metrics
~~~~~~~

``volumeFractionError`` at t = 4 (``Eshape``, ``Emass``, ``Ebound``) and the timings,
as in :doc:`disc_uni_flow`.

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/advection/discUniFlowTestsuite --smoke
   pixi run benchmark benchmarks/advection/discUniFlowTestsuite

Changed parameters
------------------

.. include:: /_generated/advection/discUniFlowTestsuite/params.rst

Larger meshes
~~~~~~~~~~~~~

The stored runs are for 100 × 60 only. A finer mesh
(``n200x120: {block_mesh_dict_config: {blocks: [{cells: [200, 1, 120]}]}}``) has no
stored TwoPhaseFlow run; for convergence use :doc:`disc_uni_flow`.

Results
-------

.. include:: /_generated/advection/discUniFlowTestsuite/plots.rst

.. include:: /_generated/advection/discUniFlowTestsuite/key_results.rst

- **MULES** reproduces TwoPhaseFlow's E1 = 0.03037 to 1.7e-14 relative (round-off).
- **isoAdvector (gradAlpha)** reproduces E1 = 0.02253 to 4.7e-9: NeoN's ``volTaylor``
  plane search stops elsewhere within ``isoFaceTol`` (1e-8) than OpenFOAM's.
- **Mass and bounds**: mass error ≤ 4e-16, alpha stays in [0, 1], on every executor.
- The testsuite's own limit E1 ≤ 0.0122 belongs to its plicRDF run; gradAlpha and
  MULES do not reach it.

Changes since the previous snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /_generated/advection/discUniFlowTestsuite/changes.rst
