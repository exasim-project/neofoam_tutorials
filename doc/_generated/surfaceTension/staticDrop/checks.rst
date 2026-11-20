17 passed, 0 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference interfoam.csv dp
     - CPU
     - **PASS**
     - max rel diff 5.8e-06 (dp n40_CPU), rtol 0.0001, 2 cases
   * - reference interfoam.csv dp
     - GPU
     - **PASS**
     - max rel diff 5.8e-06 (dp n40_GPU), rtol 0.0001, 2 cases
   * - reference interfoam.csv dp
     - Serial
     - **PASS**
     - max rel diff 5.8e-06 (dp n40_Serial), rtol 0.0001, 2 cases
   * - reference interfoam.csv maxU
     - CPU
     - **PASS**
     - max rel diff 1.5e-03 (maxU n40_CPU), rtol 0.015, 2 cases
   * - reference interfoam.csv maxU
     - GPU
     - **PASS**
     - max rel diff 1.5e-03 (maxU n40_GPU), rtol 0.015, 2 cases
   * - reference interfoam.csv maxU
     - Serial
     - **PASS**
     - max rel diff 1.5e-03 (maxU n40_Serial), rtol 0.015, 2 cases
   * - reference interfoam.csv dp_err
     - CPU
     - **PASS**
     - max rel diff 2.5e-03 (dp_err n40_CPU), rtol 0.01, 2 cases
   * - reference interfoam.csv dp_err
     - GPU
     - **PASS**
     - max rel diff 2.5e-03 (dp_err n40_GPU), rtol 0.01, 2 cases
   * - reference interfoam.csv dp_err
     - Serial
     - **PASS**
     - max rel diff 2.5e-03 (dp_err n40_Serial), rtol 0.01, 2 cases
   * - maximum dp_err
     - CPU
     - **PASS**
     - 1.798e-01 (n20_CPU), maximum 0.2
   * - maximum dp_err
     - GPU
     - **PASS**
     - 1.798e-01 (n20_GPU), maximum 0.2
   * - maximum dp_err
     - Serial
     - **PASS**
     - 1.798e-01 (n20_Serial), maximum 0.2
   * - maximum maxU_max
     - CPU
     - **PASS**
     - 4.242e-01 (n80_CPU), maximum 0.5
   * - maximum maxU_max
     - GPU
     - **PASS**
     - 4.242e-01 (n80_GPU), maximum 0.5
   * - maximum maxU_max
     - Serial
     - **PASS**
     - 4.242e-01 (n80_Serial), maximum 0.5
   * - agreement executor
     - CPU vs Serial
     - **PASS**
     - max rel diff 1.1e-10 (maxU n40_CPU), rtol 1e-08, 3 cases
   * - agreement executor
     - GPU vs Serial
     - **PASS**
     - max rel diff 6.2e-11 (maxU n40_GPU), rtol 1e-08, 3 cases
