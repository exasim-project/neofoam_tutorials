reconstruction/circle
=====================

Why and what is tested
----------------------

Interface reconstruction places a plane (normal and centre) in each interface cell from
the volume fraction alone; every geometric VoF step starts with it. This benchmark
reconstructs an exactly initialised circle once, without flow, and measures how far
NeoFOAM's ``gradAlpha`` (Youngs) PLIC planes lie from the exact circle as the mesh is
refined, next to TwoPhaseFlow's ``reconstructInterface`` on the same case (its gradAlpha
errors are numufoam's published ones, Scheufler & Roenby, arXiv 1801.05382,
sec. 4.1.1).

Case
----

.. figure:: /_static/setup/circle.png
   :alt: Sketch: a disc of radius 0.5 in the 2 x 2 square, an 8 x 8 grid, the box of the 10 random centres

   The 2 × 2 domain (x-z, one cell in y) with the coarsest grid (n = 8). Each of the
   10 samples moves the disc centre to a random point of the dashed box.

A disc of radius 0.5 with an exactly cut alpha field (``cutCellIso``), 10 random centres
per mesh. The normal error is ``1 − n · n_exact`` per cell, the centre error the
distance of the plane centre from the exact circle; L∞ is the maximum over cells and
samples, L1 the mean.

Parameter changes
-----------------

.. include:: /_generated/reconstruction/circle/params.rst

Results
-------

.. include:: /_generated/reconstruction/circle/plots.rst

.. include:: /_generated/reconstruction/circle/key_results.rst

- ``errors``: Serial, CPU, GPU and TwoPhaseFlow (dashed) lie on top of each other. The
  centre errors fall at second order (fitted slope over n8 to n1024: 1.92 in L1, 1.68
  in L∞). The normal errors stop falling at n32 and stay at about 8e-3 (L∞) and 2.4e-3
  (L1), as in TwoPhaseFlow: the accuracy of the gradAlpha normal.
- Against TwoPhaseFlow, the normal norms and centre L∞ differ by at most 4e-8
  (relative); centre L1 by up to 4.2e-6 at n1024, because the ``volTaylor`` plane
  search stops anywhere within ``isoFaceTol`` = 1e-8 of the target volume.
- ``k1``: the time of one reconstruction; the GPU is slower than Serial up to n256 and
  faster from n512 on. ``wall``: the solver wall time, 12 / 11 / 9.8 s (Serial / CPU /
  GPU) at n1024.

.. include:: /_generated/reconstruction/circle/changes.rst
