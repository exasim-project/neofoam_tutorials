.. list-table::
   :header-rows: 1
   :widths: auto

   * - Mesh
     - normal L∞
     - normal L1
     - centre L∞
     - centre L1
     - wall [s] Serial / CPU / GPU
   * - n8
     - 0.02986
     - 0.003875
     - 0.02965
     - 0.01505
     - 0.18 / 0.18 / 0.2
   * - n16
     - 0.0142
     - 0.002682
     - 0.007618
     - 0.003825
     - 0.21 / 0.18 / 0.2
   * - n32
     - 0.007495
     - 0.002409
     - 0.001926
     - 0.0009605
     - 0.23 / 0.17 / 0.23
   * - n64
     - 0.008128
     - 0.002397
     - 0.0004805
     - 0.0002403
     - 0.15 / 0.25 / 0.23
   * - n128
     - 0.008333
     - 0.002398
     - 0.0001453
     - 6.004e-05
     - 0.3 / 0.37 / 0.33
   * - n256
     - 0.008363
     - 0.002391
     - 5.19e-05
     - 1.537e-05
     - 0.7 / 0.72 / 0.78
   * - n512
     - 0.00839
     - 0.002395
     - 2.118e-05
     - 4.5e-06
     - 2.5 / 2.6 / 2.5
   * - n1024
     - 0.008392
     - 0.002395
     - 9.311e-06
     - 1.553e-06
     - 12 / 11 / 9.8

Rows: the Serial executor. CPU and GPU are bitwise identical to it in these columns.

All 24 cases and columns: :download:`results.csv </_generated/reconstruction/circle/results.csv>`, per-group checks: :download:`checks.json </_generated/reconstruction/circle/checks.json>`.
