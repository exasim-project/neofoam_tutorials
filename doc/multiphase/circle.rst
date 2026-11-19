reconstruction/circle
=====================

Interface reconstruction of a circle on hexahedral meshes. NeoFOAM's ``gradAlpha``
(Youngs) PLIC reconstruction is compared with TwoPhaseFlow's ``reconstructInterface``
and with numufoam's published errors (Scheufler & Roenby, arXiv 1801.05382,
sec. 4.1.1).

Setup
-----

.. figure:: /_static/setup/circle.png
   :alt: Sketch: a disc of radius 0.5 in the 2 x 2 square, an 8 x 8 grid, the box of the 10 random centres

   The 2 × 2 domain (x-z, one cell in y) with the coarsest grid (n = 8). Each of the
   10 samples moves the disc centre to a random point of the dashed box.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - 2 × 2 (x-z), 1 cell in y
     - ``system/blockMeshDict`` ``vertices``
   * - Disc radius R
     - 0.49999999
     - ``system/setAlphaFieldDict`` ``radius``
   * - Disc centre o
     - (1.01, 0, 1.01), drawn in [0.9 o, 1.1 o]
     - ``setAlphaFieldDict`` ``origin``; ``Random(1234567)``
   * - Samples per mesh
     - 10
     - ``system/preprocess.yaml`` ``samples``
   * - Alpha field
     - exact cut (``cutCellIso``)
     - ``setAlphaField`` tool
   * - Scheme
     - ``gradAlpha``, plane search ``volTaylor``
     - ``system/fvSolution`` ``reconstructionScheme``
   * - Plane tolerance
     - ``isoFaceTol`` 1e-8
     - ``system/fvSolution``
   * - Solver
     - ``reconstructInterface``
     - ``benchmark.yaml`` ``solver``

There is no flow and no time stepping: each sample is reconstructed once and compared
with the exact circle. The alpha field agrees with OpenFOAM-v2406's ``setAlphaField``
to round-off.

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/reconstruction/circle/``)
     - Content
   * - ``case/``
     - base case (mesh, alpha, scheme, executor)
   * - ``reference/twophaseflow.csv``
     - TwoPhaseFlow (v2506) gradAlpha sweep, n8 to n1024
   * - ``reference/numufoam_error.csv``
     - numufoam's table (isoAlpha, plicRDF, gradAlpha); its labels are shifted by one
       (``LNormal_1`` holds LNormalInf)

Metrics
~~~~~~~

TwoPhaseFlow's ``reconstructionError``, over the interface cells and the 10 samples.

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``LNormalInf``, ``LNormal1``
     - error of the interface normal
     - ``1 - n · n_exact`` per cell; ∞: max over cells and samples, 1: mean over samples
       of the mean over cells
   * - ``LCentreInf``, ``LCentre1``
     - error of the interface centre
     - distance of the reconstructed centre from the exact circle, aggregated as above
   * - ``k1``
     - time of one reconstruction [s]
     - mean wall time incl. copy to host, after one untimed warm-up
   * - ``wall_s``
     - solver wall time [s]
     - excluding imports

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/reconstruction/circle --smoke   # n8, n16 Serial
   pixi run benchmark benchmarks/reconstruction/circle           # the full sweep

Changed parameters
------------------

.. include:: /_generated/reconstruction/circle/params.rst

The full sweep takes about 1 min with ``-c 4``.

Larger meshes
~~~~~~~~~~~~~

Add ``n2048: {block_mesh_dict_config: {blocks: [{cells: [2048, 1, 2048]}]}}`` to
``mesh``. The TwoPhaseFlow table ends at n1024, so n2048 enters only the order checks
and plots. Case data grows with n² (the sweep to n1024 needs about 1.5 GB).

Results
-------

.. include:: /_generated/reconstruction/circle/plots.rst

.. include:: /_generated/reconstruction/circle/key_results.rst

- **Centre converges at 2nd order** (fitted 1.92 in centre L1, 1.68 in centre L∞), as
  numufoam's gradAlpha.
- **Normal error is flat**: L∞ stays at 8.4e-3 and L1 at 2.4e-3 from n64 on. That is the
  gradAlpha limit, in OpenFOAM as in NeoFOAM; plicRDF is not yet in NeoN.
- **Parity with TwoPhaseFlow**: the normal norms and centre L∞ agree to 4e-8; centre L1
  differs by up to 4.2e-6 at n1024 because the ``volTaylor`` plane search stops within
  ``isoFaceTol`` = 1e-8 of the target volume.
- **Executors**: Serial, CPU and GPU give identical norms; at n1024 the solver takes
  12 / 11 / 9.8 s.

Checks
~~~~~~

.. include:: /_generated/reconstruction/circle/verdicts.rst
