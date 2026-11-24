.. list-table::
   :header-rows: 1
   :widths: auto

   * - Mesh
     - max\|U\| at 0.01 s [m/s]
     - max\|U\| over t [m/s]
     - p error max
     - p error mean
   * - n16
     - 0.7298
     - 1.089
     - 0.02046
     - 0.001066
   * - n32
     - 0.6341
     - 0.873
     - 0.009866
     - 0.0002976
   * - n64
     - 0.5411
     - 0.7006
     - 0.004854
     - 9.531e-05

Rows: the Serial executor. CPU and GPU agree with it to 1e-11 (relative, in these columns; round-off values below 1e-10 left out).

All 9 cases and columns: :download:`results.csv </_generated/acceleration/tiltedBox/results.csv>`, changes against the previous snapshot: :download:`changes.json </_generated/acceleration/tiltedBox/changes.json>`.
