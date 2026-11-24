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

g = 9.81 m/s², no surface tension, isoAdvector with gradAlpha, adaptive time step
(``maxCo`` 0.2) to t = 0.1 s. Unlike TwoPhaseFlow the reconstruction is gradAlpha
instead of plicRDF and the top is open instead of closed. The pressure error is
\|p − p_hydrostatic\| over the hydrostatic range in the box.

Parameter changes
-----------------

.. include:: /_generated/acceleration/tiltedBox/params.rst

Results
-------

.. include:: /_generated/acceleration/tiltedBox/plots.rst

.. include:: /_generated/acceleration/tiltedBox/key_results.rst

- ``p_err_mean``: the mean pressure error stays nearly constant in time and falls with
  resolution, 1.3e-3, 4.1e-4, 1.8e-4 (n16, n32, n64); the largest error falls 2.0e-2,
  9.4e-3, 4.6e-3.
- ``maxU``: the spurious current at t = 0.01 is 0.70, 0.75, 0.78 m/s, 26 % (n32) and
  20 % (n64) below TwoPhaseFlow's (crosses); only the magnitude compares, as the
  setups differ. It keeps growing in time, to 3.0, 2.7, 2.0 m/s at t = 0.1.
- ``meanU``: the mean current also grows in time and is smaller on finer meshes.

.. include:: /_generated/acceleration/tiltedBox/changes.rst
