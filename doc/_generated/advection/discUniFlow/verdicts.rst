.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference numufoam.csv Eshape, celltoCellDist, Ncells
     - **PASS** 6/12 (6 skip)
     - MULES CFL01 CPU: max rel diff 6.7e-01 (Eshape MULES_CFL01_n40_CPU), rtol 1, 3 cases
     - MULES within a factor 2 of numufoam's E1; isoAdvector has no numufoam counterpart (gradAlpha), so its groups skip.
   * - maximum Emass
     - **PASS** 12/12
     - MULES CFL01 CPU: 2.776e-17 (MULES_CFL01_n40_CPU), maximum 1e-12
     - Mass is conserved to round-off.
   * - maximum Ebound
     - **PASS** 9/9
     - isoAdvector CFL01 CPU: 6.661e-16 (isoAdvector_CFL01_n20_CPU), maximum 1e-08
     - Alpha stays in [0, 1]; MULES is checked only at CFL 0.1.
