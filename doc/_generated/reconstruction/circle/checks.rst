6 passed, 3 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference twophaseflow.csv LNormalInf,LNormal1,LCentreInf,LCentre1,length,nCells
     - CPU gradAlpha
     - **FAIL**
     - max rel diff 4.2e-06 (LCentre1 n1024_CPU_gradAlpha), rtol 1e-06, 8 cases
   * - reference twophaseflow.csv LNormalInf,LNormal1,LCentreInf,LCentre1,length,nCells
     - GPU gradAlpha
     - **FAIL**
     - max rel diff 4.2e-06 (LCentre1 n1024_GPU_gradAlpha), rtol 1e-06, 8 cases
   * - reference twophaseflow.csv LNormalInf,LNormal1,LCentreInf,LCentre1,length,nCells
     - Serial gradAlpha
     - **FAIL**
     - max rel diff 4.2e-06 (LCentre1 n1024_Serial_gradAlpha), rtol 1e-06, 8 cases
   * - order LCentre1
     - CPU gradAlpha
     - **PASS**
     - 1.92 (>= 1.5)
   * - order LCentre1
     - GPU gradAlpha
     - **PASS**
     - 1.92 (>= 1.5)
   * - order LCentre1
     - Serial gradAlpha
     - **PASS**
     - 1.92 (>= 1.5)
   * - order LCentreInf
     - CPU gradAlpha
     - **PASS**
     - 1.68 (>= 1.5)
   * - order LCentreInf
     - GPU gradAlpha
     - **PASS**
     - 1.68 (>= 1.5)
   * - order LCentreInf
     - Serial gradAlpha
     - **PASS**
     - 1.68 (>= 1.5)
