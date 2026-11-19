20 passed, 0 failed, 0 skipped.

.. list-table::
   :header-rows: 1
   :widths: 30 15 10 45

   * - check
     - group
     - result
     - detail
   * - reference openfoam.csv x_r_h,Umin_xh1,Umin_xh3,Umin_xh5
     - CPU
     - **PASS**
     - max rel diff 8.8e-04 (Umin_xh5 tutorial_CPU), rtol 0.05, 2 cases
   * - reference openfoam.csv x_r_h,Umin_xh1,Umin_xh3,Umin_xh5
     - GPU
     - **PASS**
     - max rel diff 1.6e-03 (Umin_xh5 tutorial_GPU), rtol 0.05, 2 cases
   * - reference openfoam.csv x_r_h,Umin_xh1,Umin_xh3,Umin_xh5
     - Serial
     - **PASS**
     - max rel diff 1.6e-03 (Umin_xh5 tutorial_Serial), rtol 0.05, 2 cases
   * - reference openfoam.csv iterations
     - CPU
     - **PASS**
     - max rel diff 2.0e-02 (iterations coarse_CPU), rtol 0.5, 2 cases
   * - reference openfoam.csv iterations
     - GPU
     - **PASS**
     - max rel diff 4.2e-02 (iterations tutorial_GPU), rtol 0.5, 2 cases
   * - reference openfoam.csv iterations
     - Serial
     - **PASS**
     - max rel diff 2.5e-02 (iterations tutorial_Serial), rtol 0.5, 2 cases
   * - maximum profile_err
     - CPU
     - **PASS**
     - 2.293e-04 (tutorial_CPU), maximum 0.01
   * - maximum profile_err
     - GPU
     - **PASS**
     - 2.561e-04 (tutorial_GPU), maximum 0.01
   * - maximum profile_err
     - Serial
     - **PASS**
     - 2.727e-04 (tutorial_Serial), maximum 0.01
   * - maximum p_res
     - CPU
     - **PASS**
     - 5.817e-04 (tutorial_CPU), maximum 0.01
   * - maximum p_res
     - GPU
     - **PASS**
     - 5.383e-04 (tutorial_GPU), maximum 0.01
   * - maximum p_res
     - Serial
     - **PASS**
     - 4.712e-04 (tutorial_Serial), maximum 0.01
   * - maximum Ux_res
     - CPU
     - **PASS**
     - 6.054e-06 (coarse_CPU), maximum 0.001
   * - maximum Ux_res
     - GPU
     - **PASS**
     - 6.429e-06 (coarse_GPU), maximum 0.001
   * - maximum Ux_res
     - Serial
     - **PASS**
     - 6.085e-06 (coarse_Serial), maximum 0.001
   * - reference pitz_daily_1983.csv x_r_h
     - CPU
     - **PASS**
     - max rel diff 4.8e-03 (x_r_h coarse_CPU), rtol 0.2, 2 cases
   * - reference pitz_daily_1983.csv x_r_h
     - GPU
     - **PASS**
     - max rel diff 4.8e-03 (x_r_h coarse_GPU), rtol 0.2, 2 cases
   * - reference pitz_daily_1983.csv x_r_h
     - Serial
     - **PASS**
     - max rel diff 4.7e-03 (x_r_h coarse_Serial), rtol 0.2, 2 cases
   * - agreement executor
     - CPU vs Serial
     - **PASS**
     - max rel diff 6.9e-04 (Umin_xh5 tutorial_CPU), rtol 0.001, 2 cases
   * - agreement executor
     - GPU vs Serial
     - **PASS**
     - max rel diff 3.7e-04 (Umin_xh1 tutorial_GPU), rtol 0.001, 2 cases
