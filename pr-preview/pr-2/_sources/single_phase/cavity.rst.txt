singlePhase/cavity
==================

Why and what is tested
----------------------

The lid-driven cavity is the basic check of an incompressible solver: a laminar, steady
recirculating flow with a classic benchmark solution. It tests NeoFOAM's
``incompressibleFluidNeoN`` (PISO) on NeoN against the centreline velocities of Ghia,
Ghia & Shin (1982) at Re = 100, and against OpenFOAM-v2406's ``icoFoam`` on the same
case and meshes.

Case
----

.. figure:: /_static/setup/cavity.png
   :alt: Sketch: the unit square, the lid moving to the right at 1 m/s, no-slip walls, the two centrelines dashed

   The unit square (x-y, one cell in z) with the lid moving at U = 1 m/s; the dashed
   centrelines are where the velocity is compared with Ghia et al.

ν = 0.01 m²/s (Re = 100), Gauss linear, adaptive time step (``maxCo`` 0.5) to t = 20 s,
the steady state. The errors are the RMS (L2) and maximum (L∞) of u − u_Ghia and
v − v_Ghia at Ghia's 15 interior points on each centreline.

Parameter changes
-----------------

.. include:: /_generated/singlePhase/cavity/params.rst

Results
-------

.. include:: /_generated/singlePhase/cavity/plots.rst

.. include:: /_generated/singlePhase/cavity/key_results.rst

- ``profiles``: the centreline velocities lie on Ghia's points; n20 is visibly off only
  near the extrema of v.
- ``error_vs_n``: the errors are at most 1.4e-2 on n20 and 1.0e-3 to 9.1e-3 on n40 and
  n80, for velocities of order 1. u converges at order 2.9 from n20 to n40 and rises
  again on n80; v levels off at 4.5e-3 to 4.9e-3 (L2). icoFoam (dashed) does the same:
  it is 1.5 % apart on n80 and up to 19 % on n20 and n40, where the time steps differ
  (icoFoam: fixed 0.001 s). Beyond n40 the comparison is limited by Ghia's own 129 × 129
  solution.
- ``time_per_step``, ``wall_time``: the GPU is slower than Serial up to n40 and 1.8×
  faster on n80; the CPU executor is 1.26× faster on n80.

.. include:: /_generated/singlePhase/cavity/changes.rst
