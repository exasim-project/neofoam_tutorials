freeSurface/damBreak
====================

Why and what is tested
----------------------

A water column that collapses under gravity puts NeoFOAM's full two-phase solver
``incompressibleVoFNeoN`` (MULES advection, gravity across a density ratio of 1000, the
PIMPLE pressure-velocity coupling) through a fast free-surface flow. The speed of the
surge front along the floor is the classic measurable of this flow: Martin & Moyce (1952)
recorded it for collapsing columns twice as high as wide, the shape of the OpenFOAM
``damBreak`` tutorial's column. The benchmark reproduces NeoFOAM's tests
``test_damBreak_comparison`` (fixed time step) and ``test_damBreak_adaptive_time_step``
(interFoam's adaptive time step) and shows the front against the experiment and against
native interFoam on the same meshes.

Case
----

OpenFOAM's ``damBreak`` tutorial, 0.584 m × 0.584 m (x-y, one cell in z) in five blocks:
a water column a = 0.1461 m wide and 0.292 m high (n² = 2) against the left wall, an
obstacle 0.024 m wide and 0.048 m high at x = 0.292 m on the floor, walls on three sides
and an open top (``atmosphere``). Water and air (ρ = 1000/1, ν = 1e-6/1.48e-5), g =
9.81 m/s², no surface tension (σ = 0), MULES, to t = 0.2 s. The column is set with
``setFields`` (cell centres in the box), as the tutorial's ``setFieldsDict``. Both solvers
use a diagonal preconditioner for ``p_rgh`` and diagonal PBiCGStab for the MULES
corrector, as NeoFOAM's tests (NeoN's DIC factorisation fails on this matrix).

The front is the largest x of the cell centres with α > 0.5 in the bottom cells (y ≤
0.01 m; this repository's ``phaseExtent`` node), written every time step and shown as
Martin & Moyce's Z = x/a over T = n t (g/a)^½. On a mesh it moves in steps of one cell
width (ΔZ = 0.087 on ``x1``). The comparison with the experiment holds until the front
reaches the obstacle at Z = 2.0.

Reference data
~~~~~~~~~~~~~~

- ``reference/martin_moyce.csv``: Martin, J. C. & Moyce, W. J. (1952), Part IV. An
  experimental study of the collapse of liquid columns on a rigid horizontal plane,
  *Phil. Trans. R. Soc. A* 244, 312–324, Table 2 (rectangular section, n² = 2): the mean
  T at each Z of the runs with a = 1⅛ in. (28.6 mm) and a = 2¼ in. (57.2 mm). The paper
  shifts the time of every run so that T = 1.19 at Z = 1.44, as the instant of release is
  uncertain; the simulation's T counts from the release. Five points lie before the
  obstacle (Z = 1.11 … 1.89).
- ``reference/interfoam_front.csv``, ``interfoam_time_steps.csv``: interFoam of
  OpenFOAM-v2406 on this case per mesh and time step: the front at the field write times
  (every 0.01 s, the same definition) and the adaptive time steps.

Parameter changes
-----------------

.. include:: /_generated/freeSurface/damBreak/params.rst

Results
-------

.. include:: /_generated/freeSurface/damBreak/plots.rst

.. include:: /_generated/freeSurface/damBreak/key_results.rst

.. include:: /_generated/freeSurface/damBreak/changes.rst
