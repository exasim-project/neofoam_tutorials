.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference twophaseflow.csv maxU_10ms
     - **PASS** 3/3
     - CPU: max rel diff 2.6e-01 (maxU_10ms n32_CPU), rtol 0.3, 2 cases
     - Magnitude only: the setup differs from TwoPhaseFlow's (gradAlpha, open top).
   * - maximum maxU_max
     - **PASS** 3/3
     - CPU: 2.997e+00 (n16_CPU), maximum 3.5
     - Regression bound on the spurious current.
   * - maximum p_err_max
     - **PASS** 3/3
     - CPU: 2.011e-02 (n16_CPU), maximum 0.025
     - Regression bound on the hydrostatic pressure error.
   * - maximum p_err_mean
     - **PASS** 3/3
     - CPU: 1.262e-03 (n16_CPU), maximum 0.0015
     - Regression bound on the hydrostatic pressure error.
   * - agreement executor
     - **PASS** 2/2
     - CPU vs Serial: max rel diff 5.4e-15 (meanU n64_CPU), rtol 1e-08, 3 cases
     - CPU and GPU reproduce Serial.
