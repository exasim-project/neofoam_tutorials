18 passed, 0 failed, 6 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - MULES CPU
     - **PASS**
     - max rel diff 1.7e-14 (Eshape MULES_n100x60_CPU), rtol 1e-12, 1 cases
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - MULES GPU
     - **PASS**
     - max rel diff 1.7e-14 (Eshape MULES_n100x60_GPU), rtol 1e-12, 1 cases
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - MULES Serial
     - **PASS**
     - max rel diff 1.7e-14 (Eshape MULES_n100x60_Serial), rtol 1e-12, 1 cases
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CPU
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - isoAdvector GPU
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_mules.csv Eshape,celltoCellDist,Ncells
     - isoAdvector Serial
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - MULES CPU
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - MULES GPU
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - MULES Serial
     - **SKIP**
     - no stored row for these cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - isoAdvector CPU
     - **PASS**
     - max rel diff 4.7e-09 (Eshape isoAdvector_n100x60_CPU), rtol 1e-07, 1 cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - isoAdvector GPU
     - **PASS**
     - max rel diff 4.7e-09 (Eshape isoAdvector_n100x60_GPU), rtol 1e-07, 1 cases
   * - reference twophaseflow_isoadvection.csv Eshape,celltoCellDist,Ncells
     - isoAdvector Serial
     - **PASS**
     - max rel diff 4.7e-09 (Eshape isoAdvector_n100x60_Serial), rtol 1e-07, 1 cases
   * - maximum Emass
     - MULES CPU
     - **PASS**
     - 1.110e-16 (MULES_n100x60_CPU), maximum 1e-13
   * - maximum Emass
     - MULES GPU
     - **PASS**
     - 3.886e-16 (MULES_n100x60_GPU), maximum 1e-13
   * - maximum Emass
     - MULES Serial
     - **PASS**
     - 1.110e-16 (MULES_n100x60_Serial), maximum 1e-13
   * - maximum Emass
     - isoAdvector CPU
     - **PASS**
     - 4.718e-16 (isoAdvector_n100x60_CPU), maximum 1e-13
   * - maximum Emass
     - isoAdvector GPU
     - **PASS**
     - 4.718e-16 (isoAdvector_n100x60_GPU), maximum 1e-13
   * - maximum Emass
     - isoAdvector Serial
     - **PASS**
     - 4.718e-16 (isoAdvector_n100x60_Serial), maximum 1e-13
   * - maximum Ebound
     - MULES CPU
     - **PASS**
     - 3.675e-19 (MULES_n100x60_CPU), maximum 1e-08
   * - maximum Ebound
     - MULES GPU
     - **PASS**
     - 7.956e-19 (MULES_n100x60_GPU), maximum 1e-08
   * - maximum Ebound
     - MULES Serial
     - **PASS**
     - 3.675e-19 (MULES_n100x60_Serial), maximum 1e-08
   * - maximum Ebound
     - isoAdvector CPU
     - **PASS**
     - 0.000e+00 (isoAdvector_n100x60_CPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector GPU
     - **PASS**
     - 0.000e+00 (isoAdvector_n100x60_GPU), maximum 1e-08
   * - maximum Ebound
     - isoAdvector Serial
     - **PASS**
     - 0.000e+00 (isoAdvector_n100x60_Serial), maximum 1e-08
