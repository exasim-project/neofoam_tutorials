# neofoam_verification

Verification of NeoFOAM's MULES VoF advection (OpenFOAM via pybFoam, and NeoN on
Serial/CPU/GPU executors) against OpenFOAM, on TwoPhaseFlow's advection benchmarks.

```bash
pixi install
pixi run test               # 44 passed, ~6 min (the backend tests need NeoFOAM, $NEOFOAM_PYTHON, and a GPU)
pixi run update-reference   # re-runs the C++ reference, rewrites reference/
pixi run update-reconstruction-reference  # OpenFOAM-v2406 reconstruction reference, rewrites reference/curvature*/
pixi run update-advection-flux-reference  # OpenFOAM-v2406 isoAdvection face fluxes, rewrites reference/curvature*/advection/
pixi run update-isoadvection-reference    # OpenFOAM-v2406 multi-step isoAdvection, rewrites reference/*/isoAdvection/
pixi run update-twophaseflow-isoadvection-reference  # advectorVoF/isoAdvection, rewrites reference/*/*/twoPhaseFlowIsoAdvection/
pixi run benchmark benchmarks/reconstruction/circle --smoke  # the benchmark suite, below
pixi run install-neofoam [CHECKOUT]  # builds NeoFOAM (C++) into this env, below
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
| `reconstruction.py` | meshes a curvature case and runs `reference/reconstructionReference`; the `.npz` format (module docstring) and loaders |
| `advection_flux.py` | runs `reference/advectionFluxReference` on the curvature cases; the `.npz` format (module docstring) and loader |
| `isoadvection.py` | runs `reference/isoAdvectionReference` (multi-step isoAdvection) on curvature2D and the benchmarks; the `.npz` format (module docstring) and loader |
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

## Interface reconstruction (geometric VoF)

The reference for a geometric VoF port: OpenFOAM-v2406's geometricVoF
(`$OPENFOAM_BASHRC`, default `~/OpenFOAM/OpenFOAM-v2406/etc/bashrc`) on TwoPhaseFlow's
`run/benchmark/surfaceTension` cases, after `apps/benchmark/reconstructInterface`.
`reference/reconstructionReference/` is an OpenFOAM utility (wmake, at most two jobs):
alpha1 from the implicit function by `cutCellIso` (as setAlphaField), then for
`isoAlpha`, `plicRDF` and `gradAlpha` the interface normal and centre, `cutCellPLIC::calcSubCell` for
8 fixed planes per interface cell (the reconstructed one, shifted, tilted, outside the
cell, oblique), `surfaceIteratorPLIC::vofCutCell` (signed distance) for 3 normals x 4
target fractions, and TwoPhaseFlow's `reconstructionError` (normal and centre terms);
for `gradAlpha` also its least-squares gradient (the normal handed to `vofCutCell`) and
the `zoneDistribute` stencil per interface cell, whose labels past the cells are boundary
faces. `reference/<case>/{mesh,isoAlpha,plicRDF,gradAlpha}.npz` and `run.json` hold it;
the keys and
shapes are documented in `src/neofoam_verification/reconstruction.py`.

| case | mesh | cells | scheme | interface cells | LNormalInf | LNormal1 | LCentreInf | LCentre1 |
|---|---|---|---|---|---|---|---|---|
| curvature2D | 32 x 32 hex | 1024 | isoAlpha | 64 | 2.93e-03 | 3.37e-04 | 1.85e-03 | 9.48e-04 |
| | | | plicRDF | 64 | 5.21e-04 | 7.98e-05 | 1.85e-03 | 9.51e-04 |
| | | | gradAlpha | 64 | 6.38e-03 | 2.40e-03 | 1.85e-03 | 9.72e-04 |
| curvature2DTri | prisms, 32 edges per side | 2400 | isoAlpha | 110 | 2.39e-02 | 2.48e-03 | 9.00e-04 | 4.79e-04 |
| | | | plicRDF | 110 | 1.74e-03 | 2.01e-04 | 9.00e-04 | 4.89e-04 |
| | | | gradAlpha | 110 | 1.65e-02 | 2.90e-03 | 9.00e-04 | 4.76e-04 |
| curvature3D | 16^3 hex | 4096 | isoAlpha | 680 | 1.12e-02 | 1.53e-03 | 7.29e-03 | 4.65e-03 |
| | | | plicRDF | 680 | 4.66e-03 | 4.47e-04 | 7.22e-03 | 4.68e-03 |
| | | | gradAlpha | 680 | 9.16e-03 | 2.58e-03 | 7.26e-03 | 4.71e-03 |
| curvature3DTri | tets, 10 edges per side | 4685 | isoAlpha | 650 | 4.30e-01 | 3.09e-02 | 2.97e-02 | 1.12e-02 |
| | | | plicRDF | 650 | 2.54e-02 | 4.31e-03 | 3.03e-02 | 1.16e-02 |
| | | | gradAlpha | 650 | 9.55e-02 | 1.17e-02 | 3.04e-02 | 1.14e-02 |

Differences to TwoPhaseFlow's cases: smaller meshes, origin (1.01, 0, 1.01) /
(1.01, 1.01, 1.01) instead of (1, 0, 1) / (1, 1, 1), where the interface passes through
mesh points; alpha by `cutCellIso` (their `setAlphaMethod cutCellImpFunc` is TwoPhaseFlow
only); the tet block is the 2 x 2 x 2 cube of curvature3D (theirs, the unit cube, holds
an octant of the sphere); no curvature. The triangle/tet meshes are the committed
`.msh` files (gmsh 4.15.2, `pixi exec -s gmsh gmsh ...`, see the `.geo` header), so the
reference does not depend on a gmsh version. `normal()` points into the fluid
(alpha = 1), and so does the cut face's area vector. isoAlpha's iso face is not planar
on hexahedra, so its plane 0 cuts the cell's alpha only to ~1e-3 on curvature3D (to
1e-8 everywhere else). `tests/test_reconstruction.py` checks the stored files, the
Python cut cell against the initial alpha (1e-14), gradAlpha's gradient against a numpy
least-squares fit over the stored stencil, and, marked `geometricvof`, that a rerun
reproduces them bitwise.

## isoAdvection face fluxes (geometric VoF)

The unit-level reference for porting isoAdvector's advection step: one
`isoAdvection::advect` from the curvature cases' initial alpha, per scheme (isoAlpha,
plicRDF, gradAlpha), velocity (an oblique uniform one and a solid-body rotation off the
interface centre, `system/advectionFluxReferenceDict`) and Courant number (0.2, 0.5).
`reference/advectionFluxReference/` (wmake utility) runs the library's isoAdvection
twice (fvSolution `alpha.<scheme>`: nAlphaBounds 3 and clip, as interIsoFoam;
`alpha.<scheme>.unbounded`: neither) and replays `timeIntegratedFlux()` with
`cutFaceAdvectTrace.{H,C}`, a copy of `cutFaceAdvect` with trace lines only (`diff` it
against v2406's). It stops unless the trace equals the library on every face and the
replayed field equals the library's unbounded `dVf_`, both bitwise.
`reference/<case>/advection/<scheme>_<velocity>_Co<Co>.npz` holds the inputs (phi, U,
U at the points, dt, the interface and Un0), one row per `timeIntegratedFaceFlux` call
(its arguments, result, point arrival times, branch, time-integrated area and its
contributions), and the assembled fields (upwind dVf, dVf before and after
`limitFluxes`, alphaPhi, alpha unbounded and bounded); keys and shapes are documented in
`src/neofoam_verification/advection_flux.py`. `tests/test_advection_flux.py` checks
that the assembled fields follow from the rows and the inputs from the reconstruction
reference, and, marked `geometricvof`, that a rerun reproduces them bitwise.

Found on the way (a port has to reproduce them): `timeIntegratedArea` drops vertex
times within `max(1e-6 dt, 10 SMALL)` of the previous one, and its final constant phase
starts at the last vertex time, so the integration intervals need not join exactly;
the triangle-decomposition branch for non-planar faces (nShifts > 2) iterates its
`sortedOrder` indices as times (`for (const scalar timeI : order)`) and so skips the
intermediate vertex times; it is not reached on these planar meshes (every traced face
takes the nShifts 0/2 branch, none the `|Un0| <= 1e-12` one). The interface does not
reach the boundary, so no boundary face is traced.

## Multi-step isoAdvection (geometric VoF)

The parity reference for a ported isoAdvector time loop: OpenFOAM-v2406's
`isoAdvection` advects alpha as interIsoFoam does (`advect(zeroField, zeroField)`,
limitFluxes with `nAlphaBounds 3`, then clipping to [0, 1], `snapTol 0`), in
advectorVoF's time loop (dt from `maxAlphaCo` with the previous dt, capped by
`maxDeltaT`, adjusted to hit the write times; phi0 and U0 scaled by the `isoAdvector`
dict's cosine before `runTime++`). `reference/isoAdvectionReference/` (wmake utility)
runs the library with `clip false` and clips itself, so alpha before clipping is seen
every step, and counts limitFluxes' iterations with copies advected with
`nAlphaBounds` 0, 1, 2; it stops unless the copies and the library's own clipping
(step 1) agree with the run bitwise. Schemes gradAlpha and plicRDF
(`interpolateNormal false`, `iterations 10`, `tol 1e-8`; no state between steps).
`reference/<case>/isoAdvection/<scheme>[_<velocity>].npz` holds a table per step (t,
dt, Courant numbers, limitFluxes iterations, surface cells, mass/min/max before and
after clipping), alpha after step 1, at the write times (and every
`alpha_interval` steps), step 1's pieces (dVf before and after limitFluxes, alpha
after 0, 1, 2 iterations and before clipping, the interface with x0, n0 and Un0 from
`interpolationCellPoint`; U and phi for the 2D cases) and the volumeFractionError
(`metrics.py`) at the write times; keys and shapes are documented in
`src/neofoam_verification/isoadvection.py` (`load_run(label, scheme, velocity)`).
`tests/test_isoadvection.py` checks the files' consistency (time steps, iterations,
mass up to the clipping, bounds, step 1 from its face fluxes, the errors), and, marked
`geometricvof`, that a rerun reproduces them bitwise.

curvature2D's velocities are in `system/isoAdvectionReferenceDict` (`maxAlphaCo 0.5`;
translation (1, 0, 0.5) to t = 0.4, rotation omega = 1 about (1, 0, 0.8) to t = 1); the
benchmarks run their own case (meshed with v2506 as for MULES, `0/U` and `0/phi` from
the generator) to the end time, at the coarsest stored resolution. advectorVoF's
`Su = div(phi0) min(alpha, 1)` (round-off) is not passed.

| case | scheme | cells | steps | dt | iterations 0/1/2/3 | Eshape (write times) | max Emass | wall [s] |
|---|---|---|---|---|---|---|---|---|
| curvature2D translation | gradAlpha | 1024 | 20 | 0.02 | 0/18/2/0 | 6.39e-04 / 1.21e-03 | 7e-17 | 0.3 |
| | plicRDF | | 20 | | 0/19/1/0 | 1.21e-04 / 1.99e-04 | 6e-17 | 0.3 |
| curvature2D rotation | gradAlpha | 1024 | 32 | 0.030 ... 0.033 | 0/31/1/0 | 6.57e-04 / 6.83e-04 | 3e-17 | 0.3 |
| | plicRDF | | 32 | | 0/31/1/0 | 1.63e-04 / 2.21e-04 | 1e-17 | 0.3 |
| discUniFlow 100x60 | gradAlpha | 6000 | 1200 | 1/300 | 295/904/1/0 | 1.49e-02 / 1.92e-02 / 2.11e-02 / 2.25e-02 | 3e-15 | 2.5 |
| | plicRDF | | 1200 | | 271/897/32/0 | 3.17e-03 / 6.22e-03 / 9.23e-03 / 1.22e-02 | 6e-16 | 2.9 |
| vortexShearedDisc 32x32 | gradAlpha | 1024 | 431 | 0.012 ... 0.051 | 0/253/155/23 | 1.14e-01 / 5.28e-02 | 2e-13 | 1.5 |
| | plicRDF | | 431 | | 0/234/171/26 | 1.13e-01 / 4.25e-02 | 7e-13 | 2.6 |
| deformationSphere 32x32x64 | gradAlpha | 65536 | 202 | 0.0096 ... 0.05 | 0/15/78/109 | 2.76e-02 / 4.45e-03 | 8e-09 | 9.7 |
| | plicRDF | | 202 | | 0/14/74/114 | 2.76e-02 / 4.48e-03 | 8e-08 | 14 |
| Leveque 32x32x32 | gradAlpha | 32768 | 298 | 0.0064 ... 0.053 | 0/108/157/33 | 1.95e-02 / 8.54e-03 | 1e-09 | 11 |
| | plicRDF | | 299 | | 0/73/172/54 | 1.94e-02 / 7.75e-03 | 2e-08 | 18 |

(The wall time includes 1 to 3 extra advects per step that count the iterations.) The plicRDF
end values agree with the testsuite's (discUniFlow 1.22e-02 against its limit 0.0122,
deformationSphere 4.5e-03, Leveque 7.7e-03). A step whose limitFluxes leaves alpha
outside [-100 SMALL, 1 + 100 SMALL] after 3 iterations loses mass to the clipping
(Emass up to 8e-8). isoAdvection's upwind fluxes spread round-off values (< 1e-12) of
alpha over most of the domain (55 000 of 65 536 cells of deformationSphere at t = 3),
so a port compares alpha with an absolute tolerance, not by its support.

### advectorVoF with isoAdvection (benchmark context)

`python -m neofoam_verification.isoadvection --twophaseflow` runs the benchmarks with
TwoPhaseFlow's advectorVoF as for MULES (`reference.run_twophaseflow`), with
`advectionScheme isoAdvection` and the controls above (plus the testsuite's unused
`nAlphaCorr 2`, `nAlphaSubCycles 1`, `cAlpha 1`, which advectorVoF requires), and
stores `volumeFractionError.dat`, `alpha_final.txt` and `run.json` in
`reference/<case>/<resolution>/twoPhaseFlowIsoAdvection/<scheme>/` (`load_twophaseflow`).
TwoPhaseFlow's own isoAdvection on v2506, with `Su = div(phi0) min(alpha, 1)`, agrees
with the v2406 runs: Eshape to 2e-11 relative, final alpha to 3e-10
(`tests/test_isoadvection.py`). Wall time (advectorVoF, serial) next to MULES:

| case | MULES | isoAdvection gradAlpha | isoAdvection plicRDF |
|---|---|---|---|
| discUniFlow 100x60 | 2.2 s | 0.9 s | 1.2 s |
| vortexShearedDisc 32x32 | 1.5 s | 0.6 s | 0.9 s |
| deformationSphere 32x32x64 | 6.4 s | 2.4 s | 4.0 s |
| Leveque 32x32x32 | 5.1 s | 2.4 s | 4.7 s |

## Verification benchmarks (`benchmarks/<category>/<name>/`)

A benchmark is a folder of files, laid out like numufoam's `benchmarksuite/<category>/<name>/`:

| File | Contents |
|---|---|
| `benchmark.yaml` | the solver, the sweep's `dimensions` in NeoFOAM's `params.yaml` shape (dimension -> variant -> config payloads of the solver's configs), `merge` (payloads laid over the base case's config), the `smoke` subset, the `method` dimension, the `collect` spec, the declarative `checks`, the `report` columns |
| `case/` | the base case with literal values (`0/`, `system/`, `system/preprocess.yaml`) |
| `plots.py` | `plot(results: DataFrame, references: dict[str, DataFrame], out: Path)`; helpers in `suite/plots.py` (`error_plot`, `timing_plot`, `save`) |
| `reference/` | stored tables (CSV), read by the checks and handed to `plots.py` by file stem |

### Running a benchmark

```bash
pixi run benchmark FOLDER [--smoke] [--method NAME] [-c N]
```

exports the benchmark's NeoFOAM sweep (`suite/benchmark.py`: NeoFOAM's `Sweep(...,
merge=True, includes=[suite/benchmark.smk], targets=["report.md"]).export`) to
`results/<category>/<name>/` (gitignored) and runs it with one Snakemake command, which it
prints and which alone reproduces the run (in the pixi environment, OpenFOAM-v2406
sourced, as `scripts/benchmark.sh` does):

```bash
snakemake -s results/reconstruction/circle/Snakefile -d results/reconstruction/circle -c 4
```

The rules are NeoFOAM's `setup_mesh -> blockMesh` once per mesh variant (`meshes/<v>/`),
`setup` (clone of `case/`, the payloads merged in, the mesh copied, the case-level
preprocess tools run) `-> solve` (`neofoam solver <name>`) per case (`cases/<case>/`),
then `suite/benchmark.smk`'s `collect` (`results.csv`: one row per case, its variant per
dimension, renamed by `collect.columns`, and the last row of each `collect.tables`
`.dat`), `verify` (`checks.json`), `plots` (`plots/`, by the benchmark's `plots.py`) and
`report` (`report.md`: the plots, the results table, the checks). `--smoke` keeps the
`smoke` variants, `--method NAME` (repeatable) replaces the method dimension's variants by
`{NAME: {<entry>: NAME}}`. Snakemake reruns what changed (a changed `benchmark.yaml`,
`plots.py` or reference table reruns collect/verify/plots); it does not see the solver's
code: after changing a method, `--forcerun solve` on the printed command.

Checks (`suite/checks.py`), per group of cases (the dimensions but `mesh`: executor and
method): `{type: reference, file, match, columns, rtol}` (the stored table, rows matched
by the `match` columns) and `{type: order, column, spacing, minimum}` (least-squares
order over the group's resolutions).

The benchmark solvers (`solvers/`) are `neofoam.solvers` entry points (`pyproject.toml`):
a module exporting the `<name>` spec, which declares the configs a sweep may vary, and
`run(argv)`. They use NeoFOAM's models only; what they add is the benchmark's
input/output convention (here: the alpha samples in, `reconstructionError`'s `error.dat`
and a `timing.dat` with the run's wall time out). The CPU executor takes all cores unless
`OMP_NUM_THREADS` is set.

### Adding a benchmark / developing a new method

* A benchmark is a folder `benchmarks/<category>/<name>/` with the files above;
  `pixi run benchmark benchmarks/<category>/<name> --smoke` runs it.
* A new method (e.g. a reconstruction scheme registered with NeoFOAM through a
  `neofoam.plugins` entry point) needs no edit of the benchmark:
  `pixi run benchmark benchmarks/reconstruction/circle --method myScheme --smoke` runs
  the cases `n8_Serial_myScheme`, `n16_Serial_myScheme` and reports the errors and the
  checks; `reference` skips a group it has no stored row for.

### NeoFOAM in this environment

NeoFOAM is a dependency of this package (`pyproject.toml`), built from a checkout into
the pixi environment: `pixi run install-neofoam [CHECKOUT]` (default `$NEOFOAM_SRC`,
`scripts/install_neofoam.sh`) runs `pip install CHECKOUT --no-build-isolation --no-deps`
with OpenFOAM-v2406 sourced (pybFoam), `NeoN_WITH_OMP=ON NeoN_WITH_THREADS=OFF` (Kokkos
OpenMP; CUDA when `nvcc` is found; Ginkgo on by default), 4 jobs, under
`NEOFOAM_BUILD_LOCK` (default `vof_scratch/plic_bench/build.lock`). The build directory is
`.pixi/build/neofoam`, not the checkout's `_skbuild`. Compilers are the system's (gcc 13
through ccache, `/usr/local/cuda`), the ones OpenFOAM-v2406 is built with; cmake, ninja,
scikit-build-core, nanobind 3.0 and NeoFOAM's Python dependencies come from the pixi
feature `neofoam`. Then `pixi run install` registers the benchmark solvers. A first build
(vof/recon-family cf55e5b85, fresh build directory, CUDA: Kokkos, Ginkgo, NeoN) took
37 min with 4 jobs and needs about 1.6 GB for the build directory.

### reconstruction/circle

arXiv 1801.05382 (Scheufler & Roenby), sec. 4.1.1, as numufoam's
`benchmarksuite/interfaceCapturing/reconstruction/circle` (319c4b8): a disc of radius
0.49999999 in the 2 x 2 square (x-z, one cell through the empty y direction), n x n hex
cells (n = 8 ... 1024; the `mesh` dimension), schemes isoAlpha, plicRDF, gradAlpha.
TwoPhaseFlow's `reconstructInterface` reconstructs `nIter 10` samples per mesh, the
disc centred at `Random(1234567).globalPosition(0.9 o, 1.1 o)`, o = (1.01, 0, 1.01)
(`foam_random.py` reproduces the sequence to the last digit of the log), alpha by
`cutCellIso`. The errors are TwoPhaseFlow's `reconstructionError`
(`reconstruction_error.py`): per interface cell `1 - n . n_exact` (unit implicit-function
gradient at the reconstructed centre) and `distanceToSurfaces` of the centre; `*Inf` is
the largest over all cells and samples, `*1` the mean of the per-sample cell means.

`reference/numufoam_error.csv` is numufoam's stored table, verbatim. Its `getResults.py`
labels the `error.dat` columns one position off: `LNormal_1` is LNormalInf,
`LNormal_Inf` is LNormal1, `LCentre_1` is LCentreInf, `LCentre_Inf` is LCentre1
(`read_numufoam` maps them back). The case here, with TwoPhaseFlow master ba10702 on
v2506, reproduced it to 1e-11 relative (x8, x32 all schemes; x256 plicRDF). The
TwoPhaseFlow run is no longer part of the benchmark: `case/` is NeoFOAM's (literal
values, `0/`, `system/preprocess.yaml`: blockMesh, then setAlphaField with `samples: 10`;
`solvers.alpha1` holds the scheme and tolerances).

Observed order of numufoam's numbers (consecutive refinements, x8 -> x1024):
plicRDF 1.6 ... 2.8 in LNormalInf, 1.8 ... 2.6 in LNormal1, 2.0 in both centre norms;
isoAlpha's and gradAlpha's normal errors stop converging (gradAlpha's LNormalInf stays
at 2.4e-3 from x32), as in the paper.

`reference/twophaseflow.csv` is the TwoPhaseFlow (v2506) gradAlpha sweep x8 ... x1024
(stored by the earlier live TwoPhaseFlow backend, fb6a24b), all `error.dat` columns but
the timings. It agrees with numufoam to 1.9e-10 relative (LCentreInf at x1024;
`tests/test_circle_reconstruction.py`); fitted order 1.92 in
LCentre1 and 1.68 in LCentreInf (2.0 down to 1.2 between consecutive resolutions), the
normal errors do not converge. The alpha samples are NeoFOAM's `setAlphaField` tool
(`samples: 10`, time directories 1 ... 10, reconstructInterface's centres); they agree
with OpenFOAM-v2406's setAlphaField to round-off (3.9e-16 in 2 cells at x8), so the norms
equal those of the earlier OpenFOAM samples bitwise to x64 and to 5e-13 (LCentre1) above.

NeoFOAM's `reconstructInterface` (`solvers/reconstruct_interface.py`) selects the scheme
from `reconstructionSchemeNeoN` (`reconstructionSchemeNeoN.select(...).reconstruct(ops,
alpha)`), so any registered scheme runs with `--method`. With gradAlpha's default
`planeSearch volTaylor` it agrees with TwoPhaseFlow to 4e-8 relative in the normal norms
and LCentreInf at every resolution, and to 3e-7 ... 4.2e-6 in LCentre1 from x32 on (1.6e-6
at x64, 4.2e-6 at x1024): volTaylor places the plane to alpha within `isoFaceTol` 1e-8,
which moves the centre by ~1e-8 h, against an LCentre1 of 1.6e-6 at x1024. So
the `reference` check (rtol 1e-6) fails; with `planeSearch openfoam` x1024 agrees to 4e-16.
Serial, CPU and GPU give the same norms bitwise. The full sweep (8 resolutions x 3
executors, `-c 4`, `OMP_NUM_THREADS=4`) takes about 1 min and 1.5 GB in `results/`; at
x1024 the solver runs 10.5 s (Serial), 11.2 s (CPU), 10.7 s (GPU) (`wall_s`, imports
excluded), per reconstruction (k1, normal and centre copied to the host, after an
untimed ~2 s warm-up that builds the stencils) 15 / 20 / 13 ms, against 0.33 s CPU time
in TwoPhaseFlow.
