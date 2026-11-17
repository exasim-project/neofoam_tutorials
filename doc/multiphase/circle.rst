reconstruction/circle
=====================

Interface reconstruction of a circle on hexahedral meshes. NeoFOAM's ``gradAlpha``
(Youngs) PLIC reconstruction is compared with TwoPhaseFlow's ``reconstructInterface``
and with numufoam's published errors (Scheufler & Roenby, arXiv 1801.05382,
sec. 4.1.1).

Setup
-----

- A disc of radius 0.49999999 in the 2 × 2 square (x-z plane, one cell in the empty y
  direction), on n × n hex cells with n = 8, 16, …, 1024 (``mesh`` dimension).
- 10 samples per mesh. The disc centre is drawn as in TwoPhaseFlow:
  ``Random(1234567).globalPosition(0.9 o, 1.1 o)`` with o = (1.01, 0, 1.01).
- Alpha comes from NeoFOAM's ``setAlphaField`` tool (``samples: 10``, ``cutCellIso``).
  It agrees with OpenFOAM-v2406's ``setAlphaField`` to round-off.
- Solver: ``reconstructInterface``, with the scheme read from
  ``solvers.alpha1.reconstructionScheme`` (default ``gradAlpha``, plane search
  ``volTaylor``).

Inputs
~~~~~~

``benchmarks/reconstruction/circle/``:

- ``case/system/blockMeshDict``, ``case/0/alpha1``
- ``case/system/setAlphaFieldDict``: the cylinder (radius, origin, axis)
- ``case/system/preprocess.yaml``: ``blockMesh``, then ``setAlphaField`` with
  ``samples: 10``
- ``case/system/fvSolution``: the scheme and its tolerances
- ``case/system/controlDict``: the executor
- ``reference/twophaseflow.csv``: TwoPhaseFlow's (v2506) gradAlpha sweep, n8 to n1024
- ``reference/numufoam_error.csv``: numufoam's stored table (isoAlpha, plicRDF,
  gradAlpha). Its column labels are shifted by one: ``LNormal_1`` holds LNormalInf.

Metrics
~~~~~~~

These are TwoPhaseFlow's ``reconstructionError`` norms, over the interface cells and
the 10 samples:

``LNormalInf``, ``LNormal1``
   ``1 - n · n_exact`` per cell, with ``n_exact`` the unit gradient of the implicit
   function at the reconstructed centre. ``*Inf`` is the largest value over all cells
   and samples; ``*1`` is the mean over samples of each sample's mean over cells.
``LCentreInf``, ``LCentre1``
   The distance of the reconstructed interface centre from the exact circle,
   aggregated in the same way.
``k1``
   The mean wall time of one reconstruction, including the copy of normal and centre
   to the host, after one untimed warm-up.
``wall_s``
   The solver's wall time, excluding imports.

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/reconstruction/circle --smoke   # n8, n16 Serial
   pixi run benchmark benchmarks/reconstruction/circle           # the full sweep

Changed parameters
------------------

The sweep in ``benchmark.yaml``: 8 meshes × 3 executors × 1 scheme = 24 cases. The full sweep takes about 1 min with ``-c 4``. Smoke: n8 and n16 on ``Serial``.

.. list-table::
   :header-rows: 1
   :widths: 22 30 33 15

   * - Dimension
     - Variants
     - Sets (first variant)
     - Smoke
   * - ``mesh``
     - ``n8``, ``n16``, ``n32``, ``n64``, ``n128``, ``n256``, ``n512``, ``n1024``
     - ``{block_mesh_dict_config: {blocks: [{cells: [8, 1, 8]}]}}``
     - ``n8``, ``n16``
   * - ``neo_n_control_config``
     - ``Serial``, ``CPU``, ``GPU``
     - ``{executor: Serial}``
     - ``Serial``
   * - ``reconstruction_scheme_config``
     - ``gradAlpha``
     - ``{reconstructionScheme: gradAlpha}``
     - all

Larger meshes
~~~~~~~~~~~~~

Add a variant to the ``mesh`` dimension of ``benchmark.yaml``:

.. code-block:: yaml

   mesh:
     ...
     n2048: {block_mesh_dict_config: {blocks: [{cells: [2048, 1, 2048]}]}}

The stored TwoPhaseFlow table ends at n1024. A new resolution is therefore not
compared with it (the ``reference`` check matches rows on ``nCells``), but it enters
the order checks and the plots. Case data grows with n²; the full sweep up to n1024
already needs about 1.5 GB while it runs.

Results
-------

The ``errors`` plot shows the four norms against n, with TwoPhaseFlow's table dashed and
slope guides of order 1 and 2. ``k1`` and ``wall`` show the timings per executor.

.. include:: /_generated/reconstruction/circle/plots.rst

.. include:: /_generated/reconstruction/circle/results.rst

What the full sweep shows:

- **Agreement with TwoPhaseFlow.** The normal norms and ``LCentreInf`` agree to 4e-8
  relative at every resolution. ``LCentre1`` agrees to 3e-7 … 4.2e-6 from n32 on
  (1.6e-6 at n64, 4.2e-6 at n1024). The reason is the plane search: ``volTaylor``
  places the plane to within ``isoFaceTol`` = 1e-8 of the target volume, which moves
  the centre by about 1e-8 h, and that is comparable to ``LCentre1`` itself at fine
  meshes (1.6e-6 at n1024). With ``planeSearch openfoam``, n1024 agrees to 4e-16.
- **Convergence.** The centre norms converge at second order (numufoam's gradAlpha
  data: 1.92 in ``LCentre1`` and 1.68 in ``LCentreInf``). gradAlpha's normal does not
  converge: ``LNormalInf`` stays at 2.4e-3 from n32 on, in OpenFOAM as in NeoFOAM and
  as reported in the paper. plicRDF, whose normal converges at 1.6 to 2.8, is not yet
  available in NeoN.
- **Executors.** Serial, CPU and GPU give bitwise identical norms.
- **Timing at n1024.** The solver runs 10.5 s (Serial), 11.2 s (CPU) and 10.7 s (GPU).
  One reconstruction takes 15 / 20 / 13 ms, against 0.33 s of CPU time in
  TwoPhaseFlow.

Checks
~~~~~~

.. include:: /_generated/reconstruction/circle/checks.rst

Per group (executor × method):

- ``reference twophaseflow.csv`` at rtol 1e-6. This passes up to n16 and **fails on the
  full sweep** because of the ``LCentre1`` difference described above. The failure is a
  known limit of the volTaylor tolerance, not a reconstruction error.
- ``order LCentre1`` and ``order LCentreInf`` ≥ 1.5. No order is checked for the
  normal, because gradAlpha's normal does not converge.
