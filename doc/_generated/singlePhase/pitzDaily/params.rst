.. list-table::
   :header-rows: 1
   :widths: 16 40 30 14

   * - Parameter
     - Meaning
     - Values
     - Smoke run
   * - Mesh
     - cells per direction (``blockMeshDict`` blocks); shown: the first of five blocks; ``tutorial`` is OpenFOAM's mesh (12 225 cells), ``coarse`` halves every block (3 122 cells)
     - 9 × 15, 18 × 30
     - 9 × 15
   * - Executor
     - NeoN backend (``controlDict`` ``executor``)
     - Serial, CPU (OpenMP), GPU (CUDA)
     - Serial

**6 cases** (2 × 3); the smoke run (``--smoke``) has 1. The raw payloads are in ``benchmarks/singlePhase/pitzDaily/benchmark.yaml``.
