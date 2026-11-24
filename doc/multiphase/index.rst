Multiphase
==========

These benchmarks cover the building blocks of a geometric VoF solver: interface
reconstruction, interface advection, surface tension, and gravity across the interface.
Each page describes the setup, the metrics, the current results and the changes since
the previous snapshot.

.. list-table::
   :header-rows: 1
   :widths: 14 14 30 30 12

   * - Benchmark
     - Physics
     - What NeoFOAM shows
     - Status / limit
     - Serial / CPU / GPU
   * - :doc:`circle`
     - Interface reconstruction (PLIC, gradAlpha) of a circle on hex meshes
     - Agrees with TwoPhaseFlow's ``reconstructInterface`` to 4e-8 relative in the
       normal errors. The interface centre converges at second order (fitted 1.98 in
       ``LCentre1``).
     - The gradAlpha normal does not converge; OpenFOAM's gradAlpha behaves the same.
       From n32 on, ``LCentre1`` differs from TwoPhaseFlow by up to 4.2e-6. The cause
       is the volTaylor plane-search tolerance.
     - bitwise equal
   * - :doc:`disc_uni_flow`
     - Advection of a disc in uniform flow (paper setup, numufoam reference)
     - Mass is conserved to round-off (Emass ≤ 3e-17) and alpha stays bounded at
       CFL 0.1, for both isoAdvector and MULES. MULES's E1 is within 16 % of
       numufoam's at n10 and n20.
     - isoAdvector with gradAlpha does not converge on this sharp disc (E1 6.9e-3,
       7.4e-3, 8.5e-3 on n10 to n40); OpenFOAM's gradAlpha behaves the same. plicRDF
       and isoAlpha, which converge at second order, are not in NeoN yet. NeoN's MULES
       (Gauss linear normal) stalls.
     - swept; not compared
   * - :doc:`disc_uni_flow_testsuite`
     - Advection of a disc for t = 4 (TwoPhaseFlow testsuite)
     - Reproduces TwoPhaseFlow's ``advectorVoF``: MULES to 1.7e-14 and isoAdvector
       (gradAlpha) to 4.7e-9 relative in E1.
     - The testsuite's E1 limit of 0.0122 is set by plicRDF. gradAlpha (0.0225) and
       MULES (0.0304) do not reach it.
     - every executor matches TwoPhaseFlow
   * - :doc:`static_drop`
     - Surface tension: parasitic currents of a static drop (CSF)
     - At n40 it reproduces interFoam: Laplace jump 29.90 Pa against 29.9009, max
       \|U\| to 1.5 %.
     - The jump misses σ/R by 18 / 14.7 / 9.6 % at R/dx = 5 / 10 / 20, because
       gradAlpha curvature converges slowly. The spurious currents grow with
       resolution (0.15 to 0.42 m/s).
     - agree to 1e-10
   * - :doc:`tilted_box`
     - Hydrostatic balance in a tilted box (gravity, no surface tension)
     - The pressure error falls with resolution (largest 2.0e-2, 9.4e-3, 4.6e-3 of the
       hydrostatic range). max\|U\| at t = 0.01 is within 26 % of TwoPhaseFlow.
     - The spurious current grows in time, to 2.0–3.0 m/s at t = 0.1. The setup is
       not identical to TwoPhaseFlow's (gradAlpha instead of plicRDF, open top).
     - agree to 5e-15

The figures come from the results snapshot on each page or, where the snapshot is a
smoke run, from the full sweeps described there.

.. toctree::
   :maxdepth: 1

   circle
   disc_uni_flow
   disc_uni_flow_testsuite
   static_drop
   tilted_box
