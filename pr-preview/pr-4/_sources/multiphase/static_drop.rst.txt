surfaceTension/staticDrop
=========================

Why and what is tested
----------------------

Surface tension must balance the pressure jump across a curved interface without
driving a flow. A drop at rest tests exactly that in NeoFOAM's full two-phase solver
``incompressibleVoFNeoN`` (Brackbill CSF with gradAlpha curvature): every velocity is a
spurious current, and the pressure jump should equal σ/R. The case is NeoFOAM's
``stationaryDroplet`` test case; native interFoam on the same case is the reference.

Case
----

.. figure:: /_static/setup/staticDrop.png
   :alt: Sketch: a 2 mm water drop in the centre of an 8 mm box, walls on three sides, open top

   An 8 mm box (x-y, one cell in z) with a water cylinder of R = 2 mm at the centre,
   no-slip walls and an open top, on the coarsest grid (n = 20).

Water in air, σ = 0.07 N/m, no gravity, MULES, 200 fixed steps of 2e-5 s to
t = 4e-3 s. Δp is the mean pressure inside r < R/2 minus the mean outside r > 3R/2;
σ/R uses R from the water volume.

Parameter changes
-----------------

.. include:: /_generated/surfaceTension/staticDrop/params.rst

Results
-------

.. include:: /_generated/surfaceTension/staticDrop/plots.rst

.. include:: /_generated/surfaceTension/staticDrop/key_results.rst

- ``pressure_jump``: Δp = 28.84, 29.90, 31.64 Pa against σ/R ≈ 35 Pa, short by 18.0,
  14.7 and 9.6 % at R/dx = 5, 10, 20: the gradAlpha curvature converges slowly.
  interFoam gives 29.90 Pa at n40 and the same 9.6 % at n80.
- ``maxU``, ``meanU``: the spurious current over time. Its maximum over time grows with
  resolution at the fixed time step, 0.15, 0.26, 0.42 m/s (Ca up to 6.1e-3). At the end
  time on n40 max\|U\| = 0.199 m/s, interFoam's is 0.1993 m/s.

.. include:: /_generated/surfaceTension/staticDrop/changes.rst
