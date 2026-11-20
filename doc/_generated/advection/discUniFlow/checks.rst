27 passed, 0 failed, 6 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL01 CPU
     - **PASS**
     - max rel diff 6.7e-01 (Eshape MULES_CFL01_n40_CPU), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL01 GPU
     - **PASS**
     - max rel diff 6.7e-01 (Eshape MULES_CFL01_n40_GPU), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL01 Serial
     - **PASS**
     - max rel diff 6.7e-01 (Eshape MULES_CFL01_n40_Serial), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL05 CPU
     - **PASS**
     - max rel diff 5.9e-02 (Eshape MULES_CFL05_n40_CPU), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL05 GPU
     - **PASS**
     - max rel diff 5.9e-02 (Eshape MULES_CFL05_n40_GPU), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - MULES CFL05 Serial
     - **PASS**
     - max rel diff 5.9e-02 (Eshape MULES_CFL05_n40_Serial), rtol 1, 3 cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL01 CPU
     - **SKIP**
     - no stored row for these cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL01 GPU
     - **SKIP**
     - no stored row for these cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL01 Serial
     - **SKIP**
     - no stored row for these cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL05 CPU
     - **SKIP**
     - no stored row for these cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL05 GPU
     - **SKIP**
     - no stored row for these cases
   * - reference numufoam.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CFL05 Serial
     - **SKIP**
     - no stored row for these cases
   * - maximum Emass
     - MULES CFL01 CPU
     - **PASS**
     - 8.327e-17 (MULES_CFL01_n40_CPU), maximum 1e-12
   * - maximum Emass
     - MULES CFL01 GPU
     - **PASS**
     - 8.327e-17 (MULES_CFL01_n40_GPU), maximum 1e-12
   * - maximum Emass
     - MULES CFL01 Serial
     - **PASS**
     - 8.327e-17 (MULES_CFL01_n40_Serial), maximum 1e-12
   * - maximum Emass
     - MULES CFL05 CPU
     - **PASS**
     - 5.551e-17 (MULES_CFL05_n20_CPU), maximum 1e-12
   * - maximum Emass
     - MULES CFL05 GPU
     - **PASS**
     - 5.551e-17 (MULES_CFL05_n20_GPU), maximum 1e-12
   * - maximum Emass
     - MULES CFL05 Serial
     - **PASS**
     - 5.551e-17 (MULES_CFL05_n20_Serial), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL01 CPU
     - **PASS**
     - 1.388e-16 (isoAdvector_CFL01_n40_CPU), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL01 GPU
     - **PASS**
     - 6.939e-17 (isoAdvector_CFL01_n20_GPU), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL01 Serial
     - **PASS**
     - 1.388e-16 (isoAdvector_CFL01_n40_Serial), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL05 CPU
     - **PASS**
     - 5.551e-17 (isoAdvector_CFL05_n40_CPU), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL05 GPU
     - **PASS**
     - 1.388e-17 (isoAdvector_CFL05_n10_GPU), maximum 1e-12
   * - maximum Emass
     - isoAdvector CFL05 Serial
     - **PASS**
     - 5.551e-17 (isoAdvector_CFL05_n40_Serial), maximum 1e-12
   * - maximum Ebound
     - isoAdvector CFL01 CPU
     - **PASS**
     - 6.661e-16 (isoAdvector_CFL01_n20_CPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CFL01 GPU
     - **PASS**
     - 6.661e-16 (isoAdvector_CFL01_n20_GPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CFL01 Serial
     - **PASS**
     - 6.661e-16 (isoAdvector_CFL01_n20_Serial), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CFL05 CPU
     - **PASS**
     - 1.637e-15 (isoAdvector_CFL05_n40_CPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CFL05 GPU
     - **PASS**
     - 1.637e-15 (isoAdvector_CFL05_n40_GPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CFL05 Serial
     - **PASS**
     - 1.637e-15 (isoAdvector_CFL05_n40_Serial), maximum 1e-08
   * - maximum Ebound
     - MULES CFL01 CPU
     - **PASS**
     - 1.791e-18 (MULES_CFL01_n40_CPU), maximum 1e-08
   * - maximum Ebound
     - MULES CFL01 GPU
     - **PASS**
     - 1.284e-18 (MULES_CFL01_n40_GPU), maximum 1e-08
   * - maximum Ebound
     - MULES CFL01 Serial
     - **PASS**
     - 1.791e-18 (MULES_CFL01_n40_Serial), maximum 1e-08
