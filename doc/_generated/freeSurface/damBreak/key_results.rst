.. list-table::
   :header-rows: 1
   :widths: auto

   * - Time step
     - Mesh
     - steps
     - T at Z = 1.89
     - water volume change
   * - adaptive
     - x1
     - 84
     - 1.506
     - -2.428e-07
   * - adaptive
     - x2
     - 142
     - 1.332
     - -6.712e-07
   * - fixed
     - x1
     - 200
     - 1.402
     - -4.831e-07
   * - fixed
     - x2
     - 200
     - 1.344
     - -6.939e-07

Rows: the Serial executor. CPU and GPU agree with it to 1e-08 (relative, in these columns; round-off values below 1e-10 left out).

All 12 cases and columns: :download:`results.csv </_generated/freeSurface/damBreak/results.csv>`, changes against the previous snapshot: :download:`changes.json </_generated/freeSurface/damBreak/changes.json>`.
