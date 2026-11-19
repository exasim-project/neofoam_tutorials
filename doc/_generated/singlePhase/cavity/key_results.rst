.. list-table::
   :header-rows: 1
   :widths: auto

   * - Mesh
     - u error L2 [m/s]
     - u error L∞ [m/s]
     - v error L2 [m/s]
     - v error L∞ [m/s]
     - \|ΔU\| last 2 s [m/s]
     - steps
     - wall [s] Serial / CPU / GPU
   * - n20
     - 0.007298
     - 0.01352
     - 0.007151
     - 0.01046
     - 1.131e-05
     - 677
     - 2 / 2 / 9
   * - n40
     - 0.0009745
     - 0.002416
     - 0.004545
     - 0.009002
     - 1.153e-05
     - 1480
     - 15 / 15 / 30
   * - n80
     - 0.002019
     - 0.004381
     - 0.004899
     - 0.009078
     - 1.135e-05
     - 3076
     - 1.8e+02 / 1.4e+02 / 1e+02

Rows: the Serial executor. CPU and GPU agree with it to 1e-05 (relative, in these columns; round-off values below 1e-10 left out).

All 9 cases and columns: :download:`results.csv </_generated/singlePhase/cavity/results.csv>`, per-group checks: :download:`checks.json </_generated/singlePhase/cavity/checks.json>`.
