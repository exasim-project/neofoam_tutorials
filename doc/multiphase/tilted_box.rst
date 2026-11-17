acceleration/tiltedBox
======================

Hydrostatic balance in a tilted box: the spurious currents of the gravity force across
the interface, in NeoFOAM's ``incompressibleVoFNeoN``. The case is TwoPhaseFlow's
``run/benchmark/acceleration/tiltedBox`` (numufoam's ``acceleration/tiltedBox`` with
ρ = 1000/1).

Setup
-----

- The unit box tilted by 30° about y, with water below the flat interface z = 0.1345.
- g = (0, 0, -9.81), σ = 0. Water ρ = 1000, air ρ = 1.
- NeoFOAM has no ``transformPoints`` tool, so the ``blockMeshDict`` holds the rotated
  vertices. The plane initial condition comes from this repository's
  ``setAlphaPlane`` preprocess tool (an exact cut of the plane), since NeoFOAM's
  ``setAlphaField`` has no plane.
- isoAdvector with gradAlpha, adaptive time step (Co 0.2) to t = 0.1, written every
  0.005.
- Differences to TwoPhaseFlow: gradAlpha instead of plicRDF; an open top with
  ``p_rgh`` fixedValue 0 instead of a closed box with a pressure reference cell
  (``incompressibleVoFNeoN`` has no pressure reference); no momentum predictor.
- Sweep: ``mesh`` n16, n32, n64 × 3 executors = 9 cases, about 40 s. Smoke: n16
  ``Serial``.

Inputs
------

``benchmarks/acceleration/tiltedBox/``:

- ``case/system/blockMeshDict``: the rotated vertices
- ``case/system/setAlphaFieldDict``: ``type plane``, origin and normal
- ``case/system/preprocess.yaml``: ``blockMesh``, then ``setAlphaPlane``
- ``case/constant/{g,transportProperties}``, ``case/system/{controlDict,fvSolution}``
- ``metrics.py``: the metrics below, evaluated at every written time
- ``reference/twophaseflow.csv``: TwoPhaseFlow's max\|U\| at t = 0.01 (n32, n64, n128)

Metrics
-------

``maxU``, ``meanU``, ``maxU_max``
   The largest and the volume-weighted mean cell \|U\|, and the largest ``maxU`` over
   the written times. The fluids should be at rest.
``maxU_10ms``
   ``maxU`` at t = 0.01, as in TwoPhaseFlow's ``results.csv``.
``p_err_max``, ``p_err_mean``
   The largest and the volume-weighted mean ``|p - p_hydrostatic|``, relative to the
   hydrostatic pressure range in the box. ``p_hydrostatic`` is the exact solution for
   the initial interface with ``p_rgh = 0`` at the open top.

Run
---

.. code-block:: bash

   pixi run benchmark benchmarks/acceleration/tiltedBox --smoke
   pixi run benchmark benchmarks/acceleration/tiltedBox

Results
-------

``maxU`` and ``meanU`` show the spurious current over time per mesh and executor, with
TwoPhaseFlow's values at t = 0.01 as crosses. ``p_err_mean`` shows the mean pressure
error over time.

.. include:: /_generated/acceleration/tiltedBox/plots.rst

.. include:: /_generated/acceleration/tiltedBox/results.rst

- **Pressure.** The error against the hydrostatic solution falls with resolution:
  largest 2.0e-2, 9.4e-3, 4.6e-3 and mean 1.3e-3, 4.1e-4, 1.8e-4 of the hydrostatic
  range (n16, n32, n64).
- **Spurious current.** At t = 0.01, max\|U\| is 0.70, 0.75 and 0.78 m/s, which is
  26 % (n32) and 20 % (n64) below TwoPhaseFlow's 1.01 and 0.98 m/s. Since the setups
  differ (see above), only the magnitude is compared. The current grows in time, to
  3.0, 2.7 and 2.0 m/s at t = 0.1. A balanced-force reconstruction (plicRDF) is not
  yet available in NeoN.
- **Executors.** CPU and GPU agree with Serial to 5.4e-15.

Checks
------

.. include:: /_generated/acceleration/tiltedBox/checks.rst

Per executor:

- ``reference twophaseflow.csv`` on ``maxU_10ms`` at rtol 0.3: agreement in magnitude
  only.
- ``maximum maxU_max`` ≤ 3.5 m/s, ``maximum p_err_max`` ≤ 0.025 and
  ``maximum p_err_mean`` ≤ 1.5e-3: regression bounds at about 1.2 × the measured values.
- ``agreement executor`` to 1e-8.

Larger meshes
-------------

TwoPhaseFlow runs 32, 64 and 128 cells per side, and numufoam goes up to 512. Add:

.. code-block:: yaml

   mesh:
     ...
     n128: {block_mesh_dict_config: {blocks: [{cells: [128, 1, 128]}]}}

The stored TwoPhaseFlow table already holds n128, so the ``reference`` check compares
it. Another tilt angle is a mesh variant with other vertices:
``{block_mesh_dict_config: {vertices: [...], ...}}``.
