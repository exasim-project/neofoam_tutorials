14 passed, 0 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference twophaseflow.csv maxU_10ms
     - CPU
     - **PASS**
     - max rel diff 2.6e-01 (maxU_10ms n32_CPU), rtol 0.3, 2 cases
   * - reference twophaseflow.csv maxU_10ms
     - GPU
     - **PASS**
     - max rel diff 2.6e-01 (maxU_10ms n32_GPU), rtol 0.3, 2 cases
   * - reference twophaseflow.csv maxU_10ms
     - Serial
     - **PASS**
     - max rel diff 2.6e-01 (maxU_10ms n32_Serial), rtol 0.3, 2 cases
   * - maximum maxU_max
     - CPU
     - **PASS**
     - 2.997e+00 (n16_CPU), maximum 3.5
   * - maximum maxU_max
     - GPU
     - **PASS**
     - 2.997e+00 (n16_GPU), maximum 3.5
   * - maximum maxU_max
     - Serial
     - **PASS**
     - 2.997e+00 (n16_Serial), maximum 3.5
   * - maximum p_err_max
     - CPU
     - **PASS**
     - 2.011e-02 (n16_CPU), maximum 0.025
   * - maximum p_err_max
     - GPU
     - **PASS**
     - 2.011e-02 (n16_GPU), maximum 0.025
   * - maximum p_err_max
     - Serial
     - **PASS**
     - 2.011e-02 (n16_Serial), maximum 0.025
   * - maximum p_err_mean
     - CPU
     - **PASS**
     - 1.262e-03 (n16_CPU), maximum 0.0015
   * - maximum p_err_mean
     - GPU
     - **PASS**
     - 1.262e-03 (n16_GPU), maximum 0.0015
   * - maximum p_err_mean
     - Serial
     - **PASS**
     - 1.262e-03 (n16_Serial), maximum 0.0015
   * - agreement executor
     - CPU vs Serial
     - **PASS**
     - max rel diff 5.4e-15 (meanU n64_CPU), rtol 1e-08, 3 cases
   * - agreement executor
     - GPU vs Serial
     - **PASS**
     - max rel diff 4.7e-15 (meanU n32_GPU), rtol 1e-08, 3 cases
