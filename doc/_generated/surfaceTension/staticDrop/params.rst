.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per side n (n × n; ``blockMeshDict`` blocks); R/dx = n/4
     - 20, 40, 80
     - 20
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial

**9 cases** (3 × 3); the smoke run (``--smoke``) has 1. The raw payloads are in ``benchmarks/surfaceTension/staticDrop/benchmark.yaml``.
