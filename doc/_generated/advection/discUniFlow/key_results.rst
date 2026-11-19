.. list-table::
   :header-rows: 1
   :widths: auto

   * - Method
     - CFL
     - Mesh
     - E1 (shape)
     - mass error
     - bound error
     - steps
     - wall [s] Serial / CPU / GPU
   * - MULES
     - CFL01
     - n10
     - 0.01607
     - 1.388e-17
     - 2.883e-19
     - 100
     - 0.22 / 0.29 / 0.54
   * - MULES
     - CFL01
     - n20
     - 0.01094
     - 1.388e-17
     - 5.63e-19
     - 200
     - 0.38 / 0.39 / 0.51
   * - MULES
     - CFL01
     - n40
     - 0.01008
     - 2.776e-17
     - 1.791e-18
     - 400
     - 0.98 / 1.1 / 1.3
   * - MULES
     - CFL05
     - n10
     - 0.05389
     - 1.388e-17
     - 0.01455
     - 20
     - 0.27 / 0.16 / 0.26
   * - MULES
     - CFL05
     - n20
     - 0.03252
     - 1.388e-17
     - 0.01186
     - 40
     - 0.33 / 0.33 / 0.36
   * - MULES
     - CFL05
     - n40
     - 0.01928
     - 0
     - 0.008523
     - 80
     - 0.76 / 0.79 / 0.84
   * - isoAdvector
     - CFL01
     - n10
     - 0.006916
     - 2.776e-17
     - 5.242e-17
     - 100
     - 0.21 / 0.23 / 0.31
   * - isoAdvector
     - CFL01
     - n20
     - 0.007416
     - 0
     - 6.661e-16
     - 200
     - 0.37 / 0.37 / 0.52
   * - isoAdvector
     - CFL01
     - n40
     - 0.008446
     - 8.327e-17
     - 4.374e-16
     - 400
     - 0.89 / 0.93 / 1.4
   * - isoAdvector
     - CFL05
     - n10
     - 0.003953
     - 0
     - 3.275e-16
     - 20
     - 0.23 / 0.21 / 0.26
   * - isoAdvector
     - CFL05
     - n20
     - 0.007448
     - 1.388e-17
     - 8.144e-16
     - 40
     - 0.35 / 0.28 / 0.39
   * - isoAdvector
     - CFL05
     - n40
     - 0.007328
     - 0
     - 1.637e-15
     - 80
     - 0.8 / 0.76 / 0.79

Rows: the Serial executor. CPU and GPU agree with it to 5e-15 (relative, in these columns; round-off values below 1e-10 left out).

All 36 cases and columns: :download:`results.csv </_generated/advection/discUniFlow/results.csv>`, per-group checks: :download:`checks.json </_generated/advection/discUniFlow/checks.json>`.
