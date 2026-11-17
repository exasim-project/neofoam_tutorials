3 passed, 0 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference twophaseflow.csv LNormalInf,LNormal1,LCentreInf,LCentre1,length,nCells
     - Serial gradAlpha
     - **PASS**
     - max rel diff 3.8e-08 (LNormal1 n8_Serial_gradAlpha), rtol 1e-06, 2 cases
   * - order LCentre1
     - Serial gradAlpha
     - **PASS**
     - 1.98 (>= 1.5)
   * - order LCentreInf
     - Serial gradAlpha
     - **PASS**
     - 1.96 (>= 1.5)
