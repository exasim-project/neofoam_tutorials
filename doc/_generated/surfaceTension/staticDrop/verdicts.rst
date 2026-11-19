.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference interfoam.csv dp
     - **PASS** 3/3
     - CPU: max rel diff 5.8e-06 (dp n40_CPU), rtol 0.0001, 2 cases
     - The Laplace jump matches interFoam at n40.
   * - reference interfoam.csv maxU
     - **PASS** 3/3
     - CPU: max rel diff 1.5e-03 (maxU n40_CPU), rtol 0.015, 2 cases
     - The spurious current matches interFoam.
   * - reference interfoam.csv dp_err
     - **PASS** 3/3
     - CPU: max rel diff 2.5e-03 (dp_err n40_CPU), rtol 0.01, 2 cases
     - The CSF deficit of the jump matches interFoam.
   * - maximum dp_err
     - **PASS** 3/3
     - CPU: 1.798e-01 (n20_CPU), maximum 0.2
     - The jump is within 20 % of σ/R.
   * - maximum maxU_max
     - **PASS** 3/3
     - CPU: 4.242e-01 (n80_CPU), maximum 0.5
     - Regression bound on the spurious current.
   * - agreement executor
     - **PASS** 2/2
     - CPU vs Serial: max rel diff 1.1e-10 (maxU n40_CPU), rtol 1e-08, 3 cases
     - CPU and GPU reproduce Serial.
