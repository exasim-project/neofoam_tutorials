.. list-table::
   :header-rows: 1
   :widths: auto

   * - Method
     - E1 (shape)
     - mass error
     - bound error
     - steps
     - wall [s] Serial / CPU / GPU
   * - MULES
     - 0.03037
     - 5.551e-17
     - 3.675e-19
     - 1200
     - 4.9 / 5 / 3
   * - isoAdvector
     - 0.02253
     - 3.886e-16
     - 0
     - 1200
     - 2.7 / 2.8 / 3.2

Rows: the Serial executor. CPU and GPU agree with it to 3e-15 (relative, in these columns; round-off values below 1e-10 left out).

All 6 cases and columns: :download:`results.csv </_generated/advection/discUniFlowTestsuite/results.csv>`, per-group checks: :download:`checks.json </_generated/advection/discUniFlowTestsuite/checks.json>`.
