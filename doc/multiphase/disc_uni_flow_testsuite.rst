advection/discUniFlowTestsuite
==============================

TwoPhaseFlow's testsuite variant of the disc in uniform flow
(``testsuite/advection/test-discUniFlow``). It is a long run (t = 4, 1200 steps) on one
mesh, compared with stored runs of TwoPhaseFlow's ``advectorVoF`` that use the same
schemes. This is the parity test: NeoFOAM has to reproduce the C++ reference.

Setup
-----

- A disc of radius 0.25 at (0.5, 0.5) in a 5 × 3 domain (x-z), 100 × 60 cells
  (dx = 0.05), translated by U = (1, 0.5) to t = 4.
- ``maxAlphaCo 0.1`` gives a fixed dt = 1/300, i.e. 1200 steps.
- Solver: ``advectorVoF``, methods NeoN ``isoAdvector`` (gradAlpha) and NeoN
  ``MULES``.
- Sweep: 1 mesh × 3 executors × 2 methods = 6 cases. Smoke: ``Serial`` only.

Inputs
------

``benchmarks/advection/discUniFlowTestsuite/``:

- ``case/system/setAlphaFieldDict``, ``case/0/U``
- ``case/system/controlDict``: ``endTime 4``, ``maxAlphaCo 0.1``, write interval 1
- ``case/system/fvSolution``, ``case/system/fvSchemes``: the advection scheme and,
  for MULES, ``grad Gauss linear``
- ``reference/twophaseflow_mules.csv``: TwoPhaseFlow ``advectorVoF`` with
  ``MULESScheme`` (OpenFOAM-v2506)
- ``reference/twophaseflow_isoadvection.csv``: TwoPhaseFlow ``advectorVoF`` with its
  isoAdvection and gradAlpha

Metrics
-------

``volumeFractionError`` at t = 4 (``Eshape``, ``Emass``, ``Ebound``) and the
timings, as in :doc:`disc_uni_flow`.

Run
---

.. code-block:: bash

   pixi run benchmark benchmarks/advection/discUniFlowTestsuite --smoke
   pixi run benchmark benchmarks/advection/discUniFlowTestsuite

Results
-------

``E1_and_time`` shows E1 at t = 4 and the time per step per executor, with
TwoPhaseFlow's runs dashed.

.. include:: /_generated/advection/discUniFlowTestsuite/plots.rst

.. include:: /_generated/advection/discUniFlowTestsuite/results.rst

- **MULES** reproduces TwoPhaseFlow's E1 to 1.7e-14 relative (E1 = 0.03037).
- **isoAdvector with gradAlpha** reproduces it to 4.7e-9 relative (E1 = 0.02253).
  The remaining difference comes from the plane search. NeoN's ``volTaylor`` stops
  within ``isoFaceTol`` (1e-8) of the target volume, and OpenFOAM's search stops
  elsewhere in that band.
- Mass is conserved to round-off (Emass ≤ 4e-16) and alpha is bounded.
- In the full sweep, the same agreement holds on every executor.
- The testsuite's own limit, E1 ≤ 0.0122, belongs to its plicRDF run (E1 = 0.0122).
  gradAlpha and MULES do not reach it, so it is not checked. plicRDF is not yet
  available in NeoN.

Checks
------

.. include:: /_generated/advection/discUniFlowTestsuite/checks.rst

Per group (method × executor):

- ``reference twophaseflow_mules.csv`` at rtol 1e-12: round-off.
- ``reference twophaseflow_isoadvection.csv`` at rtol 1e-7: the plane-search
  tolerance.
- Each method is matched only against its own table, so the other reference is
  skipped for that group.
- ``maximum Emass`` ≤ 1e-13 and ``maximum Ebound`` ≤ 1e-8, the testsuite's
  assertions.

Larger meshes
-------------

The stored TwoPhaseFlow runs are for 100 × 60 only. A finer mesh, e.g.
``n200x120: {block_mesh_dict_config: {blocks: [{cells: [200, 1, 120]}]}}``, runs and
is checked for mass and bounds, but the reference checks skip it. For convergence
studies use :doc:`disc_uni_flow`.
