.. list-table::
   :header-rows: 1
   :widths: auto

   * - Mesh
     - cells
     - x_r / h
     - min Ux/U, x/h = 1
     - x/h = 3
     - x/h = 5
     - wall [s] Serial / CPU / GPU
   * - coarse
     - 3122
     - 6.967
     - -0.09117
     - -0.2578
     - -0.05101
     - 14 / 15 / 34
   * - tutorial
     - 12225
     - 7.025
     - -0.08755
     - -0.2462
     - -0.1602
     - 92 / 84 / 40

Rows: the Serial executor. CPU and GPU agree with it to 0.0007 (relative, in these columns; round-off values below 1e-10 left out).

All 6 cases and columns: :download:`results.csv </_generated/singlePhase/pitzDaily/results.csv>`, per-group checks: :download:`checks.json </_generated/singlePhase/pitzDaily/checks.json>`.
