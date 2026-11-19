.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per side n (n × n; ``blockMeshDict`` blocks); n80 … n320 commented out
     - 10, 20, 40
     - 10
   * - CFL (``maxAlphaCo``)
     - interface Courant number; sets the fixed dt
     - 0.1, 0.5
     - 0.1
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial
   * - Method
     - interface advection (``fvSolution`` ``advectionScheme``)
     - isoAdvector, MULES
     - all

**36 cases** (3 × 2 × 3 × 2); the smoke run (``--smoke``) has 2. The raw payloads are in ``benchmarks/advection/discUniFlow/benchmark.yaml``.
