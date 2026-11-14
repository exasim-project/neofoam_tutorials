# neofoam_verification

Verification of NeoFOAM's MULES VoF advection (OpenFOAM via pybFoam, and NeoN on
Serial/CPU/GPU executors) against OpenFOAM, on TwoPhaseFlow's advection benchmarks.

```bash
pixi install
pixi run test               # 44 passed, ~6 min (the backend tests need NeoFOAM, $NEOFOAM_PYTHON, and a GPU)
pixi run update-reference   # re-runs the C++ reference, rewrites reference/
```

## Layout

| Path | Contents |
|---|---|
| `cases/<name>/` | the benchmark case (OpenFOAM format): blockMeshDict, `0.orig`, setAlphaFieldDict, MULES controls, controlDict with the `volumeFractionError` function object; for a generated velocity also the testsuite's generator application (`generateU*/`, built with wmake into `$FOAM_USER_APPBIN`) |
| `reference/<name>/<resolution>/` | the OpenFOAM MULES reference: `volumeFractionError.dat` (C++, verbatim), `alpha_final.txt`, `run.json` |
| `src/neofoam_verification/benchmarks.py` | the registry: case dir, initial shape (cylinder, sphere), prescribed velocity (uniform, or generated with its `isoAdvector` time dependence), end time, write interval, resolutions |
| `foam.py` | foamlib readers, OpenFOAM's face/cell geometry in numpy |
| `shapes.py`, `cut_cell.py` | implicit functions; TwoPhaseFlow's `cutCellIso` (exact volume fraction) |
| `metrics.py` | TwoPhaseFlow's `volumeFractionError` (Eshape, Emass, Ebound) on arrays |
| `reference.py` | meshes a case (blockMesh, setAlphaField, generator) and runs TwoPhaseFlow's `advectorVoF` |
| `backend.py` | `run_case(benchmark, backend, executor, case_dir) -> RunResult`, the adapter to `neofoam.algorithms.vof` |

## Reference

TwoPhaseFlow master ba10702, built for OpenFOAM-v2506 (`~/OpenFOAM/<user>-v2506`;
v2406 has no TwoPhaseFlow build, `$TWOPHASEFLOW_BASHRC` selects another one): `advectorVoF`
with `advectionScheme MULESScheme`. Meshes and initial fields from v2406 and v2506 are
identical. TwoPhaseFlow's MULESScheme is interFoam's `alphaEqn.H` (the explicit
branch here) except that `advectorVoF` passes the source `Su = div(phi) min(alpha, 1)`,
which is round-off for a solenoidal velocity, and it does not sub-cycle.

### discUniFlow (testsuite/advection/test-discUniFlow)

Disc r = 0.25 at (0.5, 0.5) in a 5 x 3 domain (x-z, 100 x 60 x 1 cells, dx = 0.05,
`front`/`back` empty), translated with the uniform U = (1, 0, 0.5) to t = 4
(alpha `rim` fixedValue 0, U `rim` zeroGradient). Time step from `maxAlphaCo 0.1`
(`maxCo 1e10`, no ramping, adjusted to hit the write times): dt = 1/300, 1200 steps,
about 3 s. Settings differing from the testsuite, which runs isoAdvector/plicRDF:
`advectionScheme MULESScheme`, `MULESCorr no`, `nLimiterIter 3`,
`div(phirb,alpha) Gauss linear` (was `Gauss interfaceCompression`, unused there),
`grad Gauss linear` (was `pointCellsLeastSquares`), write precision 17, uncompressed.

| t | Eshape | Emass | Ebound |
|---|---|---|---|
| 1 | 1.7353e-02 | 2.8e-17 | 1.3e-18 |
| 2 | 2.2773e-02 | 2.8e-17 | 1.5e-18 |
| 3 | 2.6200e-02 | 8.3e-17 | 2.7e-19 |
| 4 | 3.0369e-02 | 1.4e-16 | 3.8e-19 |

The testsuite limits (Eshape <= 0.0122, Emass <= 1e-13, Ebound <= 1e-8) are tuned
for isoAdvector; the MULES values are reported, not asserted against them.

### Time-dependent benchmarks (vortexShearedDisc, deformationSphere, Leveque)

The velocity is written by the testsuite's own generator applications, compiled
against v2506 (`cases/<name>/generateU*/`, sources unchanged): `mesh_case` runs
`wmake` and the generator after setAlphaField, so advectorVoF and the library read the
same `0/U` and `0/phi`. generateUVortex2D integrates the point stream function along
the face edges (divergence-free to round-off); generateUDeform and generateU evaluate U
at the face centres and project phi with `CorrectPhi` (a pcorr PCG solve), which is not
practical to transcribe bitwise. advectorVoF reads `phi` (createPhi) and scales it each
step after setDeltaT: `phi = phi0 cos(2 pi (t + dt/2)/period)` (`period`) or
`phi0 cos(pi (t + dt/2)/spirallingFlow)`, from the `isoAdvector` dict of fvSolution.

| case | testsuite | here (default; also stored) | flow | end, write interval |
|---|---|---|---|---|
| vortexShearedDisc | x-z unit square, 32 ... 512 | 128x128; 32x32, 64x64, 256x256 | `period 16` | 8, 4 |
| deformationSphere | 1 x 1 x 2 box, res x res x 2 res, 32 ... 128 | 32x32x64 | `spirallingFlow 3` | 3, 1.5 |
| Leveque | unit cube, res^3, 32 ... 128 | 32x32x32 | `spirallingFlow 3` | 3, 1.5 |

The 64 resolutions of the 3D cases (12 MB / 6 MB of stored alpha) are not stored.
Differences to the testsuite, besides MULES (as discUniFlow): `div(phirb,alpha) Gauss
linear`, vortexShearedDisc's `grad Gauss linear` (the 3D cases use Gauss linear
already), blockMesh only (no cube.fms/meshDict), serial (the testsuite also runs 4
MPI ranks), write precision 17 uncompressed, `startFrom startTime`, `runTimeModifiable
no`. `maxAlphaCo 0.5`, `maxDeltaT 0.05`, `nAlphaCorr 2`, `cAlpha 1` are the testsuite's.

advectorVoF can abort with a double free after printing `End` (TwoPhaseFlow's libVoF
and libpostProcess and v2506's libgeometricVoF free the same static type-name words at
exit); `reference.py` accepts that exit when the log shows `End`.

C++ reference (volumeFractionError.dat):

| case | t | Eshape | Emass | Ebound |
|---|---|---|---|---|
| vortexShearedDisc 128x128 | 4 | 1.1507e-01 | 5.6e-17 | 1.7e-09 |
| | 8 | 1.1310e-02 | 5.6e-17 | 7.6e-04 |
| deformationSphere 32x32x64 | 1.5 | 2.7558e-02 | 7.6e-17 | 9.3e-08 |
| | 3 | 7.1063e-03 | 6.6e-17 | 6.4e-03 |
| Leveque 32x32x32 | 1.5 | 1.9437e-02 | 2.0e-16 | 2.7e-09 |
| | 3 | 9.0341e-03 | 1.9e-16 | 9.0e-08 |

For reference, the testsuite's isoAdvector/plicRDF Eshape at the end time are
2.3e-03 (vortexShearedDisc 128, plicRDF), 4.5e-03 (deformationSphere 32) and 7.7e-03
(Leveque 32); they are not asserted. (vortexShearedDisc at t = 4 is compared, as by
the function object, with the initial disc.)

MULES is not bounded here: with the testsuite's `nAlphaCorr 2` the second corrector's
upwind flux is built from the first corrector's alpha but applied to the old one, and
alpha leaves [0, 1] by up to 6e-3 (deformationSphere); `nLimiterIter 10` or `50`
change nothing, `nAlphaCorr 1` reduces it to ~1e-5. The library has to reproduce the
reference's Ebound (tests/test_backend.py).

vortexShearedDisc's final field is ill-conditioned: scaling the initial alpha by
(1 - 1e-14) changes the C++ reference's alpha at t = 8 by 6.4e-5 / 9.1e-10 / 4.3e-5 /
1.2e-3 (32 / 64 / 128 / 256 cells per side; 8e-9 at t = 4 for 128), in filament cells
with alpha ~1e-4. The library's differences to the reference are of that size, so the
final field is held to 1e-4 at 128x128; Eshape and Ebound still agree to 1e-11. The 3D
cases respond with 2e-13 / 5e-14 and the library matches them to 1e-13.

## Metrics

`metrics.py` transcribes `volumeFractionError.C`: Eshape = sum V |alpha - alphaExact|
(absolute, not normalised), Emass = |sum V alpha - initial mass|, Ebound =
|max(-min alpha, max alpha - 1)|; alphaExact is the cut-cell volume fraction of the
initial shape moved by U0 t when |U| is uniform. Against the C++ output of the same
run (`tests/test_metrics.py`): Eshape to 1e-15 relative, Ebound bitwise, Emass to a
few ulps of the total volume. The timing columns (tRec, Tadv) are not reproduced.

## Adding a benchmark

A case directory under `cases/` plus a `Benchmark` entry in `benchmarks.py`;
`tests/test_benchmarks.py` checks that the two agree.
