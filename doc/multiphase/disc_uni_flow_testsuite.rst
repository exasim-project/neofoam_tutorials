advection/discUniFlowTestsuite
==============================

Why and what is tested
----------------------

The parity case for advection: TwoPhaseFlow's testsuite variant of the disc in uniform
flow (``testsuite/advection/test-discUniFlow``), a long run of 1200 steps on one mesh.
It shows how closely NeoN's isoAdvector (``gradAlpha``) and MULES reproduce TwoPhaseFlow's
``advectorVoF`` with the same schemes, whose stored runs are the reference. For
convergence with resolution see :doc:`disc_uni_flow`.

Case
----

.. figure:: /_static/setup/discUniFlowTestsuite.png
   :alt: Sketch: a disc of radius 0.25 moving from (0.5, 0.5) to (4.5, 2.5) in a 5 x 3 domain

   The 5 × 3 domain (x-z, one cell in y) with its 100 × 60 grid. The disc moves from
   (0.5, 0.5) to (4.5, 2.5).

A disc of radius 0.25 moves with the fixed velocity U = (1, 0.5) for t = 4, with
``maxAlphaCo`` 0.1 (1200 steps). E1 is ``Σ V |alpha − alpha_exact|`` at t = 4, as in
:doc:`disc_uni_flow`.

Parameter changes
-----------------

.. include:: /_generated/advection/discUniFlowTestsuite/params.rst

Results
-------

.. include:: /_generated/advection/discUniFlowTestsuite/plots.rst

.. include:: /_generated/advection/discUniFlowTestsuite/key_results.rst

- ``E1_and_time`` (left): every executor's E1 lies on TwoPhaseFlow's (dashed). MULES
  reproduces E1 = 0.03037 to 1.8e-14 relative (round-off); isoAdvector reproduces
  E1 = 0.02253 to 4.7e-9, because NeoN's ``volTaylor`` plane search stops elsewhere
  within ``isoFaceTol`` (1e-8) than OpenFOAM's.
- On every executor the mass error is ≤ 4.8e-16 and alpha stays in [0, 1] to 8e-19.
- ``E1_and_time`` (right): the solver wall time per step.

.. include:: /_generated/advection/discUniFlowTestsuite/changes.rst
