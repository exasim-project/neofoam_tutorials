.. list-table::
   :header-rows: 1
   :widths: 24 16 30 30

   * - Check
     - Groups
     - Detail (first such group)
     - Why
   * - reference openfoam.csv x_r_h, Umin_xh1, Umin_xh3, Umin_xh5
     - **PASS** 3/3
     - CPU: max rel diff 8.8e-04 (Umin_xh5 tutorial_CPU), rtol 0.05, 2 cases
     - Same case, mesh and iterations as OpenFOAM's simpleFoam.
   * - reference openfoam.csv iterations
     - **PASS** 3/3
     - CPU: max rel diff 2.0e-02 (iterations coarse_CPU), rtol 0.5, 2 cases
     - The convergence rate depends on the linear solvers (Ginkgo here, GAMG / smoothSolver in OpenFOAM).
   * - maximum profile_err
     - **PASS** 3/3
     - CPU: 2.293e-04 (tutorial_CPU), maximum 0.01
     - The velocity profiles match OpenFOAM's.
   * - maximum p_res
     - **PASS** 3/3
     - CPU: 5.817e-04 (tutorial_CPU), maximum 0.01
     - Converged to the tutorial's residual tolerance.
   * - maximum Ux_res
     - **PASS** 3/3
     - CPU: 6.054e-06 (coarse_CPU), maximum 0.001
     - Converged to the tutorial's residual tolerance.
   * - reference pitz_daily_1983.csv x_r_h
     - **PASS** 3/3
     - CPU: max rel diff 4.8e-03 (x_r_h coarse_CPU), rtol 0.2, 2 cases
     - Loose sanity check against the experiment.
   * - agreement executor
     - **PASS** 2/2
     - CPU vs Serial: max rel diff 6.9e-04 (Umin_xh5 tutorial_CPU), rtol 0.001, 2 cases
     - CPU and GPU reproduce Serial.
