acceleration/tiltedBox
======================

Why and what is tested
----------------------

Gravity acting across a density ratio of 1000 must give a hydrostatic pressure, not a
flow. In a box tilted against the mesh, the interface cuts the cells obliquely, so any
imbalance of the gravity force in NeoFOAM's ``incompressibleVoFNeoN`` shows up as a
spurious current and a pressure error. The case is TwoPhaseFlow's
``run/benchmark/acceleration/tiltedBox`` (numufoam's ``acceleration/tiltedBox`` with
ρ = 1000/1); TwoPhaseFlow's stored max\|U\| at t = 0.01 is the reference.

Case
----

.. figure:: /_static/setup/tiltedBox.png
   :alt: Sketch: the unit box tilted by 30 degrees, water below the horizontal plane z = 0.1345, gravity downwards

   The unit box (x-z, one cell in y) tilted by 30°, with water below the horizontal
   interface z = 0.1345, slip walls and an open top, on the coarsest grid (n = 16).

g = 9.81 m/s², no surface tension, MULES, adaptive time step (``maxCo`` 0.2) to
t = 0.1 s. Unlike TwoPhaseFlow the advection is MULES instead of isoAdvector with
plicRDF and the top is open instead of closed. Geometric VoF variants follow once
NeoFOAM's VoF stack has them; the previous snapshot ran isoAdvector with gradAlpha. The pressure error is
\|p − p_hydrostatic\| over the hydrostatic range in the box.

Parameter changes
-----------------

.. include:: /_generated/acceleration/tiltedBox/params.rst

Results
-------

.. include:: /_generated/acceleration/tiltedBox/plots.rst

.. include:: /_generated/acceleration/tiltedBox/key_results.rst

- ``p_err_mean``: the mean pressure error stays nearly constant in time and falls with
  resolution, 1.1e-3, 3.0e-4, 9.5e-5 (n16, n32, n64, at t = 0.1); the largest error
  falls 2.0e-2, 9.9e-3, 4.9e-3, as with isoAdvector before.
- ``maxU``: the spurious current at t = 0.01 is 0.73, 0.63, 0.54 m/s, 37 % (n32) and
  45 % (n64) below TwoPhaseFlow's (crosses); only the magnitude compares, as the
  setups differ. After t ≈ 0.02 it grows only slowly, to 1.06, 0.87, 0.70 m/s at
  t = 0.1, about a third of isoAdvector's 3.0, 2.7, 2.0 m/s in the previous snapshot.
- ``meanU``: the mean current grows slowly in time and is smaller on finer meshes, by
  about half per refinement.

.. include:: /_generated/acceleration/tiltedBox/changes.rst
