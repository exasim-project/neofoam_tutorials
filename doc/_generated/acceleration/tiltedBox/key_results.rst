.. list-table::
   :header-rows: 1
   :widths: auto

   * - Mesh
     - max\|U\| at 0.01 s [m/s]
     - max\|U\| over t [m/s]
     - p error max
     - p error mean
   * - n16
     - 0.6965
     - 2.997
     - 0.02011
     - 0.001262
   * - n32
     - 0.7499
     - 2.686
     - 0.009415
     - 0.000411
   * - n64
     - 0.7848
     - 2.003
     - 0.004615
     - 0.0001793

Rows: the Serial executor. CPU and GPU agree with it to 4e-12 (relative, in these columns; round-off values below 1e-10 left out).

All 9 cases and columns: :download:`results.csv </_generated/acceleration/tiltedBox/results.csv>`, per-group checks: :download:`checks.json </_generated/acceleration/tiltedBox/checks.json>`.
