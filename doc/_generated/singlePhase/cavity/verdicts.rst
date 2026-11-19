.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference icofoam.csv u_L2, u_Linf, v_L2, v_Linf
     - **PASS** 3/3
     - CPU: max rel diff 1.9e-01 (v_Linf n20_CPU), rtol 0.2, 3 cases
     - NeoN reproduces OpenFOAM icoFoam's errors (the coarse meshes differ by the time step, which the PISO steady state depends on weakly).
   * - order u_L2
     - **PASS** 3/3
     - CPU: 2.90 (>= 1.5)
     - Second order from n20 to n40; at n80 the error reaches Ghia's own, also for icoFoam.
   * - maximum u_Linf
     - **PASS** 3/3
     - CPU: 1.352e-02 (n20_CPU), maximum 0.05
     - Regression bound on the coarsest mesh's error.
   * - maximum v_Linf
     - **PASS** 3/3
     - CPU: 1.046e-02 (n20_CPU), maximum 0.05
     - Regression bound on the coarsest mesh's error.
   * - maximum dU
     - **PASS** 3/3
     - CPU: 1.153e-05 (n40_CPU), maximum 5e-05
     - The run reached the steady state.
   * - agreement executor
     - **PASS** 2/2
     - CPU vs Serial: max rel diff 5.5e-08 (u_L2 n40_CPU), rtol 0.0001, 3 cases
     - CPU and GPU reproduce Serial (iterative solves to 1e-8).
