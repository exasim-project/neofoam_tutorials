.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per direction (``blockMeshDict`` blocks)
     - 100 × 60
     - all
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial
   * - Method
     - interface advection (``fvSolution`` ``advectionScheme``)
     - isoAdvector, MULES
     - all

**6 cases** (1 × 3 × 2); the smoke run (``--smoke``) has 2. The raw payloads are in ``benchmarks/advection/discUniFlowTestsuite/benchmark.yaml``.
