singlePhase/pitzDaily
=====================

Why and what is tested
----------------------

A turbulent, separated flow solved to the steady state: the backward-facing step of
Pitz & Daily (1983) with k-ε and wall functions. It tests NeoFOAM's
``incompressibleFluidNeoN`` (SIMPLE) with NeoN's k-ε closure and Ginkgo linear solvers
against OpenFOAM-v2406's ``simpleFoam`` on the same case and meshes, and loosely against
the measured reattachment length x_r / h ≈ 7.0.

Case
----

.. figure:: /_static/setup/pitzDaily.png
   :alt: Sketch: the inlet channel, the step of height h on the lower wall, the channel tapering to the outlet, the profile stations at x/h = 1, 3, 5, 7

   OpenFOAM's ``pitzDaily`` geometry (x-y, one cell in z): inlet at the left, the step
   of height h = 25.4 mm at x = 0, the outlet at the right; the dashed lines are the
   profile stations.

Inlet U = 10 m/s, ν = 1e-5 m²/s (Re_h = 25 400); NeoFOAM's ``pitzDaily_steady``
tutorial, i.e. OpenFOAM's tutorial with plain SIMPLE (p relaxed by 0.3). NeoN has no
``residualControl``, so every case runs 1500 iterations; ``iterations`` in
``results.csv`` is where the tutorial's tolerances are first met. x_r is where the
near-wall Ux behind the step turns positive.

Parameter changes
-----------------

.. include:: /_generated/singlePhase/pitzDaily/params.rst

Results
-------

.. include:: /_generated/singlePhase/pitzDaily/plots.rst

.. include:: /_generated/singlePhase/pitzDaily/key_results.rst

- ``profiles``: Ux / U_inlet at x/h = 1, 3, 5, 7 on both meshes, NeoFOAM (solid) on
  top of OpenFOAM (dashed); the largest RMS difference is 2.7e-4 of U_inlet, and the
  backflow minima differ by at most 0.2 %.
- ``reattachment``: x_r / h = 6.967 (coarse) and 7.025 (tutorial) against OpenFOAM's
  6.967 and 7.021, both within 0.5 % of the measured 7.0 on every executor.
- ``residuals``: the tutorial's tolerances (dotted) are first met after 348 (coarse)
  and 844 (tutorial) iterations on Serial, against OpenFOAM's 356 and 866; afterwards
  the p residual falls no further (4e-4 to 6e-4 at the last iteration).
- ``wall_time``: the wall time of the 1500 iterations.

.. include:: /_generated/singlePhase/pitzDaily/changes.rst
