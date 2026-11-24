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
     - 1.11e-16
     - 3.675e-19
     - 1200
     - 5 / 5.1 / 3.1
   * - isoAdvector
     - 0.02253
     - 4.718e-16
     - 0
     - 1200
     - 2.9 / 2.9 / 3.3

Rows: the Serial executor. CPU and GPU are bitwise identical to it in these columns.

All 6 cases and columns: :download:`results.csv </_generated/advection/discUniFlowTestsuite/results.csv>`, changes against the previous snapshot: :download:`changes.json </_generated/advection/discUniFlowTestsuite/changes.json>`.
