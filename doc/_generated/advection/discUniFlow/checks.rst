5 passed, 0 failed, 1 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL01 Serial
     - **PASS**
     - max rel diff 1.6e-01 (Eshape MULES_CFL01_n10_Serial), rtol 1, 1 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL01 Serial
     - **SKIP**
     - no stored row for these cases
   * - maximum Emass
     - MULES CFL01 Serial
     - **PASS**
     - 1.388e-17 (MULES_CFL01_n10_Serial), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL01 Serial
     - **PASS**
     - 2.776e-17 (isoAdvector_CFL01_n10_Serial), maximum 1e-12
   * - maximum Ebound
     - isoAdvector CFL01 Serial
     - **PASS**
     - 5.242e-17 (isoAdvector_CFL01_n10_Serial), maximum 1e-08
   * - maximum Ebound
     - MULES CFL01 Serial
     - **PASS**
     - 2.883e-19 (MULES_CFL01_n10_Serial), maximum 1e-08
