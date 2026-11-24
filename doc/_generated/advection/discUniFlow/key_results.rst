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
     - 0
     - 2.883e-19
     - 100
     - 0.3 / 0.25 / 0.35
   * - MULES
     - CFL01
     - n20
     - 0.01094
     - 2.776e-17
     - 5.63e-19
     - 200
     - 0.4 / 0.46 / 0.56
   * - MULES
     - CFL01
     - n40
     - 0.01008
     - 8.327e-17
     - 1.791e-18
     - 400
     - 1.1 / 1.1 / 1.3
   * - MULES
     - CFL05
     - n10
     - 0.05389
     - 0
     - 0.01455
     - 20
     - 0.28 / 0.23 / 0.27
   * - MULES
     - CFL05
     - n20
     - 0.03252
     - 5.551e-17
     - 0.01186
     - 40
     - 0.36 / 0.38 / 0.41
   * - MULES
     - CFL05
     - n40
     - 0.01928
     - 5.551e-17
     - 0.008523
     - 80
     - 0.85 / 0.87 / 0.91
   * - isoAdvector
     - CFL01
     - n10
     - 0.006916
     - 0
     - 5.242e-17
     - 100
     - 0.27 / 0.28 / 0.37
   * - isoAdvector
     - CFL01
     - n20
     - 0.007416
     - 5.551e-17
     - 6.661e-16
     - 200
     - 0.4 / 0.43 / 0.58
   * - isoAdvector
     - CFL01
     - n40
     - 0.008446
     - 1.388e-16
     - 4.374e-16
     - 400
     - 0.93 / 0.95 / 1.2
   * - isoAdvector
     - CFL05
     - n10
     - 0.003953
     - 2.776e-17
     - 3.275e-16
     - 20
     - 0.28 / 0.23 / 0.28
   * - isoAdvector
     - CFL05
     - n20
     - 0.007448
     - 1.388e-17
     - 8.144e-16
     - 40
     - 0.36 / 0.36 / 0.42
   * - isoAdvector
     - CFL05
     - n40
     - 0.007328
     - 5.551e-17
     - 1.637e-15
     - 80
     - 0.86 / 0.86 / 0.91

Rows: the Serial executor. CPU and GPU agree with it to 8e-14 (relative, in these columns; round-off values below 1e-10 left out).

All 36 cases and columns: :download:`results.csv </_generated/advection/discUniFlow/results.csv>`, changes against the previous snapshot: :download:`changes.json </_generated/advection/discUniFlow/changes.json>`.
