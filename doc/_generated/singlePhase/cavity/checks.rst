17 passed, 0 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference icofoam.csv u_L2,u_Linf,v_L2,v_Linf
     - CPU
     - **PASS**
     - max rel diff 1.9e-01 (v_Linf n20_CPU), rtol 0.2, 3 cases
   * - reference icofoam.csv u_L2,u_Linf,v_L2,v_Linf
     - GPU
     - **PASS**
     - max rel diff 1.9e-01 (v_Linf n20_GPU), rtol 0.2, 3 cases
   * - reference icofoam.csv u_L2,u_Linf,v_L2,v_Linf
     - Serial
     - **PASS**
     - max rel diff 1.9e-01 (v_Linf n20_Serial), rtol 0.2, 3 cases
   * - order u_L2
     - CPU
     - **PASS**
     - 2.90 (>= 1.5)
   * - order u_L2
     - GPU
     - **PASS**
     - 2.90 (>= 1.5)
   * - order u_L2
     - Serial
     - **PASS**
     - 2.90 (>= 1.5)
   * - maximum u_Linf
     - CPU
     - **PASS**
     - 1.352e-02 (n20_CPU), maximum 0.05
   * - maximum u_Linf
     - GPU
     - **PASS**
     - 1.352e-02 (n20_GPU), maximum 0.05
   * - maximum u_Linf
     - Serial
     - **PASS**
     - 1.352e-02 (n20_Serial), maximum 0.05
   * - maximum v_Linf
     - CPU
     - **PASS**
     - 1.046e-02 (n20_CPU), maximum 0.05
   * - maximum v_Linf
     - GPU
     - **PASS**
     - 1.046e-02 (n20_GPU), maximum 0.05
   * - maximum v_Linf
     - Serial
     - **PASS**
     - 1.046e-02 (n20_Serial), maximum 0.05
   * - maximum dU
     - CPU
     - **PASS**
     - 1.153e-05 (n40_CPU), maximum 5e-05
   * - maximum dU
     - GPU
     - **PASS**
     - 1.153e-05 (n40_GPU), maximum 5e-05
   * - maximum dU
     - Serial
     - **PASS**
     - 1.153e-05 (n40_Serial), maximum 5e-05
   * - agreement executor
     - CPU vs Serial
     - **PASS**
     - max rel diff 5.5e-08 (u_L2 n40_CPU), rtol 0.0001, 3 cases
   * - agreement executor
     - GPU vs Serial
     - **PASS**
     - max rel diff 1.8e-08 (u_Linf n40_GPU), rtol 0.0001, 3 cases
