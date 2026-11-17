advection/discUniFlow
=====================

A disc translated in a uniform flow: the paper's advection test (Scheufler & Roenby,
arXiv 1801.05382, sec. 4.2.1, as in numufoam). It compares NeoN's isoAdvector
(``gradAlpha`` reconstruction) and NeoN's MULES with numufoam's stored errors, over
resolution and Courant number.

Setup
-----

- A disc of radius 0.2 at (0.25, 0.25) in the unit square (x-z, one cell thick),
  translated by U = (1, 1) for t = 0.5.
- Solver: ``advectorVoF`` with a fixed time step from ``maxAlphaCo`` (``maxCo`` off, as
  in numufoam).
- Sweep: ``mesh`` n10, n20, n40 × ``CFL`` (``maxAlphaCo``) 0.1, 0.5 × executor ×
  ``method`` isoAdvector, MULES = 36 cases, about 1.5 min with ``-c 1``. numufoam's
  finer meshes (n80 to n320) and CFLs 0.05 and 0.2 are commented-out variants in
  ``benchmark.yaml``.
- Smoke: n10, CFL 0.1, ``Serial``, both methods.

Inputs
------

``benchmarks/advection/discUniFlow/``:

- ``case/system/setAlphaFieldDict``: the disc
- ``case/0/U``: the uniform velocity
- ``case/system/controlDict``: ``endTime 0.5``, ``maxAlphaCo``, ``writeInterval``,
  and the ``volumeFractionError`` function object's write interval
- ``case/system/fvSolution``: ``advectionScheme`` and the alpha controls
- ``reference/numufoam.csv``: numufoam's ``error.csv`` (isoAlpha, plicRDF and MULES
  at CFL 0.05 to 0.5, n10 to n320)

Metrics
-------

These are TwoPhaseFlow's ``volumeFractionError`` at t = 0.5:

``Eshape`` (E1)
   ``Σ V |alpha - alpha_exact|``, absolute, not normalised. ``alpha_exact`` is the
   ``cutCellIso`` volume fraction of the initial disc moved by ``U t``.
``Emass``
   ``|Σ V alpha - initial mass|``.
``Ebound``
   ``max(-min alpha, max alpha - 1)``.
``Tadv``, ``wall_s``, ``steps``
   The wall time per alpha advection, the solver's wall time, and the number of steps.

Run
---

.. code-block:: bash

   pixi run benchmark benchmarks/advection/discUniFlow --smoke
   pixi run benchmark benchmarks/advection/discUniFlow -c 1

Results
-------

``E1_vs_n`` shows E1 against n per CFL, with numufoam's isoAlpha, plicRDF and MULES
dashed. ``E1_vs_CFL`` shows E1 against CFL per method. ``time_per_step`` shows the
advection and solver time per step.

.. include:: /_generated/advection/discUniFlow/plots.rst

.. include:: /_generated/advection/discUniFlow/results.rst

What the sweep shows:

- **Mass and bounds.** Mass is conserved to round-off for both methods. Alpha stays
  in [0, 1] for isoAdvector, and for MULES up to CFL 0.1. At CFL 0.5, MULES
  overshoots (Ebound 0.11 at n320; numufoam's MULES gives 0.12).
- **MULES against numufoam.** NeoN's MULES is 0.84–1.05 × numufoam's E1 at n10 and n20.
  The ratio grows to 1.1–1.8 × at n40 and 3.5 × at n320 (CFL 0.1). The two differ
  only in the interface-normal gradient: NeoN uses Gauss linear, numufoam
  ``pointCellsLeastSquares``. NeoN's MULES stalls (observed order 0.7 from n40 to n320
  at CFL 0.1, none at CFL 0.5), while OpenFOAM's MULES with ``pointCellsLeastSquares``
  is first order.
- **isoAdvector with gradAlpha does not converge on this case.** At CFL 0.1, E1 is
  6.9e-3, 7.4e-3 and 8.5e-3 on n10, n20 and n40, and the observed order from n40 to
  n320 is 0.8. numufoam ran no gradAlpha case; its isoAlpha and plicRDF are other
  reconstructions, so the plots compare trends only.

Is NeoFOAM's isoAdvector wrong? No. On the same setup, NeoFOAM reproduces OpenFOAM /
TwoPhaseFlow's ``advectorVoF``: isoAdvector with gradAlpha to 2e-9, and MULES with a
Gauss linear gradient to 1e-15 (see also :doc:`disc_uni_flow_testsuite`). OpenFOAM's
gradAlpha does not converge on this sharp disc either. The second-order
reconstructions, plicRDF and isoAlpha, are not yet in NeoN. The alpha fields at
t = 0.5 on n40 show the difference:

.. figure:: /_static/discuniflow/isoAdvector_n40_neofoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, NeoFOAM isoAdvector gradAlpha, n40

   NeoFOAM, isoAdvector with gradAlpha, n40, maxAlphaCo 0.1: E1 = 8.4e-3. The error
   (right) reaches ±0.5 in cells along the whole interface.

.. figure:: /_static/discuniflow/plicRDF_n40_openfoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, OpenFOAM isoAdvector plicRDF, n40

   OpenFOAM-v2506, isoAdvector with plicRDF, same case: E1 = 7.7e-4, with errors below
   ±0.06. This is the reconstruction NeoN still needs.

Checks
------

.. include:: /_generated/advection/discUniFlow/checks.rst

Per group (method × CFL × executor):

- ``reference numufoam.csv`` with rtol 1.0 on ``Eshape``. Only MULES has a
  counterpart; the isoAdvector groups are skipped. The default meshes pass. **The
  finer meshes fail this band** (3.5 × at n320) because of the stalling Gauss linear
  normal.
- ``maximum Emass`` ≤ 1e-12 (the testsuite asserts 1e-13).
- ``maximum Ebound`` ≤ 1e-8 for isoAdvector, and for MULES at CFL ≤ 0.1 only (the
  ``where`` filter), since MULES is not bounded at larger CFL.
- No ``order`` check is enabled. On n10 to n40, neither method converges. A commented
  check (order ≥ 0.6 on n40 to n320) can be enabled together with the finer meshes.

Larger meshes
-------------

Uncomment the variants in ``benchmark.yaml``:

.. code-block:: yaml

   mesh:
     ...
     n80: {block_mesh_dict_config: {blocks: [{cells: [80, 1, 80]}]}}
     n160: {block_mesh_dict_config: {blocks: [{cells: [160, 1, 160]}]}}
     n320: {block_mesh_dict_config: {blocks: [{cells: [320, 1, 320]}]}}

and, optionally, the order check
``{type: order, column: Eshape, spacing: celltoCellDist, minimum: 0.6, where: {mesh:
[n40, n80, n160, n320]}}``. n320 needs about 20 MB per case and 1–4 min on ``Serial``
per CFL. Expect the ``reference`` check to fail there for MULES (see above).
