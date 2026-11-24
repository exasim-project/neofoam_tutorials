advection/discUniFlow
=====================

Why and what is tested
----------------------

Advection must move a sharp interface without smearing it, losing mass or leaving
[0, 1]. Here a disc is translated by a uniform velocity, so the exact solution is the
same disc moved by U t, and the shape error over resolution and Courant number measures
NeoN's isoAdvector (``gradAlpha`` reconstruction) and NeoN's MULES. This is the paper's
advection test (Scheufler & Roenby, arXiv 1801.05382, sec. 4.2.1); numufoam's stored
errors for MULES, isoAlpha and plicRDF are the reference.

Case
----

.. figure:: /_static/discuniflow/isoAdvector_n40_neofoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, NeoFOAM isoAdvector gradAlpha, n40

   NeoFOAM, isoAdvector with gradAlpha, n40, maxAlphaCo 0.1: alpha (left) and
   alpha − alpha_exact (right) at the start and at t = 0.5.

A disc of radius 0.2 starts at (0.25, 0.25) in the unit square (x-z, one cell in y)
and moves with the fixed velocity U = (1, 1) to (0.75, 0.75) at t = 0.5; only alpha is
transported, with a fixed time step set by ``maxAlphaCo``. E1 is
``Σ V |alpha − alpha_exact|`` at t = 0.5.

Parameter changes
-----------------

.. include:: /_generated/advection/discUniFlow/params.rst

Results
-------

.. include:: /_generated/advection/discUniFlow/plots.rst

.. include:: /_generated/advection/discUniFlow/key_results.rst

- ``E1_vs_n``: numufoam's isoAlpha and plicRDF (dashed) fall by a factor of about 10
  from n10 to n40. NeoN's isoAdvector with gradAlpha does not: at CFL 0.1 its E1 is
  6.9e-3, 7.4e-3, 8.4e-3 on n10, n20, n40. NeoN's MULES at CFL 0.1 is 0.84 and 0.92 ×
  numufoam's MULES on n10 and n20 and 1.67 × on n40; the two differ in the interface
  normal's gradient (NeoN: Gauss linear, numufoam: ``pointCellsLeastSquares``).
- ``E1_vs_CFL``: MULES's E1 grows with the Courant number, as numufoam's does.
- Mass is conserved to round-off (mass error ≤ 1.4e-16) by both methods. isoAdvector
  stays in [0, 1]; MULES does at CFL 0.1 and leaves it by up to 1.5e-2 at CFL 0.5.
- ``time_per_step``: the advection and the solver wall time per step.

The case figure shows where the isoAdvector error sits: at t = 0.5 alpha − alpha_exact
reaches ±0.5 in cells along the whole interface. OpenFOAM-v2506's isoAdvector with
plicRDF, which NeoN does not have yet, on the same case:

.. figure:: /_static/discuniflow/plicRDF_n40_openfoam.png
   :alt: alpha and alpha - alpha_exact at t = 0 and t = 0.5, OpenFOAM isoAdvector plicRDF, n40

   OpenFOAM-v2506, isoAdvector with plicRDF, n40, maxAlphaCo 0.1: E1 = 7.7e-4, with
   errors below ±0.06.

.. include:: /_generated/advection/discUniFlow/changes.rst
