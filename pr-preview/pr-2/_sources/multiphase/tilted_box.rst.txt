acceleration/tiltedBox
======================

Hydrostatic balance in a tilted box: the spurious currents of the gravity force across
the interface, in NeoFOAM's ``incompressibleVoFNeoN``. The case is TwoPhaseFlow's
``run/benchmark/acceleration/tiltedBox`` (numufoam's ``acceleration/tiltedBox`` with
ρ = 1000/1).

Setup
-----

.. figure:: /_static/setup/tiltedBox.png
   :alt: Sketch: the unit box tilted by 30 degrees, water below the horizontal plane z = 0.1345, gravity downwards

   The unit box (x-z, one cell in y) tilted by 30°, with water below the horizontal
   interface z = 0.1345, slip walls and an open top, on the coarsest grid (n = 16).

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Quantity
     - Value
     - Where set
   * - Domain
     - unit box tilted by 30° about y
     - ``system/blockMeshDict`` (rotated ``vertices``)
   * - Interface
     - plane z = 0.1345, water below
     - ``system/setAlphaFieldDict`` (``type plane``)
   * - Gravity g
     - (0, 0, −9.81) m/s²
     - ``constant/g``
   * - Surface tension σ
     - 0
     - ``constant/transportProperties``
   * - Water ρ, ν
     - 1000 kg/m³, 1e-6 m²/s
     - ``constant/transportProperties``
   * - Air ρ, ν
     - 1 kg/m³, 1.48e-5 m²/s
     - ``constant/transportProperties``
   * - Alpha advection
     - isoAdvector, gradAlpha
     - ``system/fvSolution``
   * - Pressure–velocity
     - no momentum predictor, 6 correctors
     - ``system/fvSolution`` ``PIMPLE``
   * - Time step, end time
     - adaptive, ``maxCo`` 0.2; 0.1 s
     - ``system/controlDict``
   * - Samples
     - every 0.005 s
     - ``controlDict`` ``writeInterval``; ``postProcess.yaml`` (``stepper``)

The fluids should stay at rest. NeoFOAM has no ``transformPoints``, so the mesh is
rotated in ``blockMeshDict``, and the plane comes from this repository's
``setAlphaPlane`` tool. Unlike TwoPhaseFlow: gradAlpha instead of plicRDF, and an open
top (``p_rgh`` fixedValue 0) instead of a closed box with a pressure reference.

Inputs
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File (``benchmarks/acceleration/tiltedBox/``)
     - Content
   * - ``case/``
     - base case (rotated mesh, plane, g, phases, schemes)
   * - ``case/system/postProcess.yaml``
     - the in-situ tables: ``maxU``, ``magU_integral``, ``p_err_max``,
       ``p_err_integral``, ``volume``, at every written time
   * - ``metrics.py``
     - ``derive``: the means, ``maxU_max`` and ``maxU_10ms`` from the tables
   * - ``reference/twophaseflow.csv``
     - TwoPhaseFlow's max\|U\| at t = 0.01 (n32, n64, n128)

Metrics
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Metric
     - Meaning
     - Formula
   * - ``maxU``, ``meanU``
     - spurious current [m/s]
     - max and volume-weighted mean of cell \|U\| (``mag | max``; ``mag | volIntegrate``
       over ``area | sum``: the rotated cells differ in volume by 1e-6)
   * - ``maxU_max``
     - largest spurious current over time
     - max over written times of ``maxU``
   * - ``maxU_10ms``
     - TwoPhaseFlow's measure
     - ``maxU`` at t = 0.01
   * - ``p_err_max``, ``p_err_mean``
     - hydrostatic pressure error
     - max and volume-weighted mean of ``|p − p_hydrostatic|`` / hydrostatic range in the
       box (this repository's ``hydrostaticError`` node, then ``max``; ``volIntegrate``
       over ``area | sum``)

Run
~~~

.. code-block:: bash

   pixi run benchmark benchmarks/acceleration/tiltedBox --smoke
   pixi run benchmark benchmarks/acceleration/tiltedBox

Changed parameters
------------------

.. include:: /_generated/acceleration/tiltedBox/params.rst

The full sweep takes about 40 s.

Larger meshes
~~~~~~~~~~~~~

Add ``n128: {block_mesh_dict_config: {blocks: [{cells: [128, 1, 128]}]}}``; the
TwoPhaseFlow table already holds n128. Another tilt angle is a mesh variant with other
``vertices``.

Results
-------

.. include:: /_generated/acceleration/tiltedBox/plots.rst

.. include:: /_generated/acceleration/tiltedBox/key_results.rst

- **Pressure converges**: the largest error falls 2.0e-2, 9.4e-3, 4.6e-3 and the mean
  1.3e-3, 4.1e-4, 1.8e-4 of the hydrostatic range (n16, n32, n64).
- **Spurious current**: 0.70, 0.75, 0.78 m/s at t = 0.01, 26 % (n32) and 20 % (n64)
  below TwoPhaseFlow — only the magnitude is comparable, the setups differ.
- **It grows in time**, to 3.0, 2.7, 2.0 m/s at t = 0.1; a balanced-force
  reconstruction (plicRDF) is not yet in NeoN.
- **Executors**: CPU and GPU agree with Serial to 5e-15.

Changes since the previous snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: /_generated/acceleration/tiltedBox/changes.rst
