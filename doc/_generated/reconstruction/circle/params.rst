.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per side n (n × n; ``blockMeshDict`` blocks)
     - 8, 16, 32, 64, 128, 256, 512, 1024
     - 8, 16
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial
   * - Method
     - interface reconstruction (``fvSolution`` ``reconstructionScheme``)
     - gradAlpha
     - all

**24 cases** (8 × 3 × 1); the smoke run (``--smoke``) has 2. The raw payloads are in ``benchmarks/reconstruction/circle/benchmark.yaml``.
