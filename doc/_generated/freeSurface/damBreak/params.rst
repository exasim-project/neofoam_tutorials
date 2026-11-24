.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per direction (``blockMeshDict`` blocks); shown: the first of five blocks; ``x1`` is OpenFOAM's tutorial mesh (2 268 cells), ``x2`` doubles every block (9 072 cells)
     - 23 × 8, 46 × 16
     - 23 × 8
   * - Time step (``adjustTimeStep``)
     - fixed ``deltaT`` or adaptive (``maxCo``, ``maxAlphaCo``); fixed: ``deltaT`` 1e-3; adaptive: ``maxCo`` = ``maxAlphaCo`` = 1
     - False, True
     - True
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial

**12 cases** (2 × 2 × 3); the smoke run (``--smoke``) has 1. The raw payloads are in ``benchmarks/freeSurface/damBreak/benchmark.yaml``.
