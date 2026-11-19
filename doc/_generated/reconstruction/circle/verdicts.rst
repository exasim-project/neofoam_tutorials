.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference twophaseflow.csv LNormalInf, LNormal1, LCentreInf, LCentre1, length, nCells
     - **FAIL** 3/3
     - CPU gradAlpha: max rel diff 4.2e-06 (LCentre1 n1024_CPU_gradAlpha), rtol 1e-06, 8 cases
     - Fails on the fine meshes: LCentre1 differs by up to 4.2e-6 (n1024) because volTaylor stops within isoFaceTol (1e-8) of the target volume; the normal norms agree to 4e-8.
   * - order LCentre1
     - **PASS** 3/3
     - CPU gradAlpha: 1.92 (>= 1.5)
     - The interface centre converges at second order, as in numufoam.
   * - order LCentreInf
     - **PASS** 3/3
     - CPU gradAlpha: 1.68 (>= 1.5)
     - Same for the largest centre error.
