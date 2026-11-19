.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference twophaseflow_mules.csv Eshape, celltoCellDist, Ncells
     - **PASS** 3/6 (3 skip)
     - MULES CPU: max rel diff 1.7e-14 (Eshape MULES_n100x60_CPU), rtol 1e-12, 1 cases
     - NeoN MULES reproduces TwoPhaseFlow to round-off.
   * - reference twophaseflow_isoadvection.csv Eshape, celltoCellDist, Ncells
     - **PASS** 3/6 (3 skip)
     - isoAdvector CPU: max rel diff 4.7e-09 (Eshape isoAdvector_n100x60_CPU), rtol 1e-07, 1 cases
     - isoAdvector reproduces TwoPhaseFlow within the plane-search tolerance.
   * - maximum Emass
     - **PASS** 6/6
     - MULES CPU: 5.551e-17 (MULES_n100x60_CPU), maximum 1e-13
     - The testsuite's mass assertion.
   * - maximum Ebound
     - **PASS** 6/6
     - MULES CPU: 3.675e-19 (MULES_n100x60_CPU), maximum 1e-08
     - The testsuite's boundedness assertion.
