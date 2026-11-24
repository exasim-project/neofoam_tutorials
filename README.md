# neofoam_tutorials

A showcase of NeoFOAM's verification state: TwoPhaseFlow's benchmarks (and a few
others) rerun with NeoFOAM on NeoN's Serial/CPU/GPU executors, shown next to stored
reference data of OpenFOAM, TwoPhaseFlow, numufoam and the literature (committed CSV
tables). The suite does not judge the results; it only flags a result that changed
drastically against the documentation's snapshot. TwoPhaseFlow and the OpenFOAM
reference codes are not needed.

```bash
pixi install
pixi run test               # the unit tests: no NeoFOAM run, no external code
pixi run benchmark benchmarks/reconstruction/circle --smoke  # the benchmark suite, below
pixi run install-neofoam [CHECKOUT]  # builds NeoFOAM (C++) into this env, below
pixi run docs               # syncs results/ into doc/_generated/, builds the docs
```

## Layout

| Path | Contents |
|---|---|
| `benchmarks/<category>/<name>/` | the benchmarks (below), with their own tests (`test_*.py`) |
| `src/neofoam_tutorials/suite/` | the benchmark suite: export to a NeoFOAM sweep, the Snakemake rules and workers, the change flag (`changes.py`), plots, report |
| `src/neofoam_tutorials/solvers/`, `postprocess/`, `tools/` | the NeoFOAM solvers, postProcess members and preprocess tool the benchmarks run |
| `src/neofoam_tutorials/metrics.py`, `cut_cell.py`, `reconstruction_error.py` | TwoPhaseFlow's `volumeFractionError` (Eshape, Emass, Ebound), `cutCellIso` and `reconstructionError` in numpy |
| `test/` | unit tests of `src/neofoam_tutorials/`, mirroring it |
| `doc/` | the documentation, with the committed results snapshot `doc/_generated/` |

`metrics.py` transcribes `volumeFractionError.C`: Eshape = sum V |alpha - alphaExact|
(absolute, not normalised), Emass = |sum V alpha - initial mass|, Ebound =
|max(-min alpha, max alpha - 1)|; alphaExact is the cut-cell volume fraction of the
initial shape moved by U0 t when |U| is uniform. The timing columns (tRec, Tadv) are not
reproduced.

## Verification benchmarks (`benchmarks/<category>/<name>/`)

A benchmark is a folder of files, laid out like numufoam's `benchmarksuite/<category>/<name>/`:

| File | Contents |
|---|---|
| `benchmark.yaml` | the solver, the sweep's `dimensions` in NeoFOAM's `params.yaml` shape (dimension -> variant -> config payloads of the solver's configs), `merge` (payloads laid over the base case's config), the `smoke` subset, the `method` dimension, the `collect` spec, the `report` columns |
| `case/` | the base case with literal values (`0/`, `system/`, `system/preprocess.yaml`; `system/postProcess.yaml`: NeoFOAM's in-situ tables, below) |
| `plots.py` | `plot(results: DataFrame, references: dict[str, DataFrame], out: Path)`; helpers in `suite/plots.py` (`error_plot`, `timing_plot`, `histories`, `profiles`, `save`) |
| `reference/` | stored tables (CSV) of other codes and the literature, handed to `plots.py` by file stem |
| `metrics.py` | optional: what the in-situ tables cannot do. `derive(history: DataFrame, case: Path) -> DataFrame`, columns derived from a case's tables at collect (`collect.derive`), and/or `metrics(case: Path) -> DataFrame`, one row per written time from the case's log, fields or tables, per case after the solve (`metrics: {script, prune}`) |

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
snakemake -s results/reconstruction/circle/Snakefile -d results/reconstruction/circle -c 4 report.md
```

The rules are NeoFOAM's `setup_mesh -> blockMesh` once per mesh variant (`meshes/<v>/`),
`setup` (clone of `case/`, the payloads merged in, the mesh copied, the case-level
preprocess tools run) `-> solve` (`neofoam solver <name>`) per case (`cases/<case>/`),
then `suite/benchmark.smk`'s `collect`, `compare` (`changes.json`), `plots` (`plots/`, by
the benchmark's `plots.py`) and `report` (`report.md`: the plots, the results table, the
changes). On success the cases and meshes are removed. `--smoke` keeps the `smoke`
variants, `--method NAME` (repeatable) replaces the method dimension's variants by
`{NAME: {<entry>: NAME}}`.

`collect` reads per case its `collect.tables` -- NeoFOAM `postProcess` CSVs
(`postProcessing/<table>.csv`, `time` first) and function-object `.dat` files -- and
merges them on the time (to 12 significant digits, as NeoFOAM's CSV writes it; a later
table's column replaces an earlier one of the same name; NeoFOAM's empty-selection
sentinel +-1e15 is read as NaN), then adds the `collect.derive` script's columns: the
case's history. It writes `results.csv` (one row per case, its variant per dimension,
renamed by `collect.columns`, then the last row of its history), with `history: true`
`histories.csv` (every row of every case's history, with its variant columns) and with
`profiles: [files]` `profiles.csv` (those per-case tables concatenated, e.g. the final
profiles a `metrics.py` writes):

```yaml
collect:
  tables: [postProcessing/maxU.csv, postProcessing/volumeFractionError/0/timing.dat]
  derive: metrics.py          # derive(history, case) -> history
  history: true               # histories.csv
  profiles: [postProcessing/profiles.csv]   # profiles.csv
  columns: {mesh: mesh, neo_n_control_config: executor}
```

Only `collect` (and `metrics`) read the cases: `compare`, `plots` and `report` read
`results.csv`, `histories.csv` and `profiles.csv` (`suite/plots.py`'s `histories()` and
`profiles()`), so a benchmark's plots never read a case folder. Snakemake reruns what
changed: a changed `plots.py`, reference table or snapshot reruns compare/plots/report alone,
also after the cases are gone; `collect` reruns on a change of the `collect` section
(its `params`) or the derive script, and then needs the cases (it reruns the solves once
they are removed). The command targets `report.md`: the Snakefile's default `all` also
wants every `cases/<case>/done` and would rerun the solves once they are removed. It does
not see the solver's code: after changing a method, `--forcerun solve` on the printed
command.

With `metrics` in `benchmark.yaml`, a per-case rule `metrics` runs after `solve`: it
writes the script's table as `cases/<case>/postProcessing/metrics.dat` (a function-object
`.dat`, which `collect.tables` names) and, with `prune: true`, removes the case's time
directories but the first and the last.

### In-situ tables (NeoFOAM's `postProcess`)

A case's `system/postProcess.yaml` declares NeoFOAM's in-situ tables (NeoFOAM's
`doc/reference/postprocessing.rst`): per table a source, a pipeline of nodes and a write
control; the solver appends a row per evaluation to `postProcessing/<name>.csv`. The NeoN
solvers (incompressibleVoFNeoN, incompressibleFluidNeoN, and this repository's advectorVoF,
which steps `post_process` after `write_output` as incompressibleVoFNeoN) support only the
`internal` source, on the registry fields (`alpha1`, `U`, `p_rgh`, `p`, `rho`). The
benchmarks evaluate their tables at the field write times (`write_control_type: stepper`)
or the function object's (`runTime`). This repository registers, through the
`neofoam.plugins` entry point `neofoam_tutorials.postprocess` (`pyproject.toml`):

| `type` | kind | what |
|---|---|---|
| `shapeError` | source | `\|alpha - alpha_exact\|` per cell (NeoFOAM's `cutCellIso` of the implicit function moved by `U0 t`), `volIntegrate` it for TwoPhaseFlow's Eshape |
| `startField` | source | a field as written at the start time (`volIntegrate` of `alpha.water`: the initial mass of Emass) |
| `hydrostaticError` | node | `\|p - p_hydrostatic\|` over the hydrostatic range, for a flat interface |
| `change` | node | the largest component of `\|U - U_previous\|` since the table's previous evaluation |

They compute on the host (NeoN binds no element-wise difference), the NeoFOAM nodes on
the field's executor.

The change flag (`suite/changes.py`, the workflow's `compare`): `results.csv` against the
documentation's snapshot `doc/_generated/<category>/<name>/results.csv`, rows matched by
the dimension columns. A numeric column is flagged when new/old leaves [0.5, 2] (a sign
change too) or turns NaN, a case when it is missing in the run; a case only in the run
is listed as new. `changes.json`, the report and the docs show the findings; the
workflow never fails on them.

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
  the cases `n8_Serial_myScheme`, `n16_Serial_myScheme` and reports the errors; against
  the snapshot they are new cases.

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
The case here, with TwoPhaseFlow master ba10702 on
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
`benchmarks/reconstruction/circle/test_reference.py`); fitted order 1.92 in
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
which moves the centre by ~1e-8 h, against an LCentre1 of 1.6e-6 at x1024; with
`planeSearch openfoam` x1024 agrees to 4e-16.
Serial, CPU and GPU give the same norms bitwise. The full sweep (8 resolutions x 3
executors, `-c 4`, `OMP_NUM_THREADS=4`) takes about 1 min (1.5 GB of case data while it runs, removed on success); at
x1024 the solver runs 10.5 s (Serial), 11.2 s (CPU), 10.7 s (GPU) (`wall_s`, imports
excluded), per reconstruction (k1, normal and centre copied to the host, after an
untimed ~2 s warm-up that builds the stencils) 15 / 20 / 13 ms, against 0.33 s CPU time
in TwoPhaseFlow.

### advection/discUniFlow, advection/discUniFlowTestsuite

TwoPhaseFlow's `advectorVoF` on NeoFOAM (`solvers/advector_vof.py`, `neofoam solver
advectorVoF`): a subset of `incompressibleVoFNeoN` (runtime, solution loop, field writer,
the `advectionModelNeoN` member of fvSolution's `advectionScheme`: NeoN isoAdvector with
`reconstructionScheme gradAlpha`, or NeoN MULES; `0/U` read, `phi = flux(U)`, no pressure
or surface-force member). The time step is fixed: `adaptiveTimeStepNeoN`'s
`courant_limit` (setDeltaT.H's undamped `maxAlphaCo` target) is contributed as the
`initialTimeStepConstraint`, so the first step takes it (controlDict `deltaT` is the
ceiling) and no damped constraint changes it later; for a uniform velocity that is
advectorVoF's step. It writes TwoPhaseFlow's `volumeFractionError.dat` (`metrics.py` on
the solver's alpha at the function object's `writeInterval`; `tRec` 0, `Tadv` the wall
time per alpha advection) and `timing.dat` (`wall_s`, `steps`), and evaluates the case's
`postProcess` tables after each field write. Eshape, Emass and Ebound in `results.csv`
come from the tables (`case/system/postProcess.yaml`: `shapeError | volIntegrate`, the
water volume `alpha1 | volIntegrate` and its start value `startField | volIntegrate`,
`alpha1 | min`, `max`; Emass and Ebound derived by the benchmark's `metrics.py`), and
replace the `.dat`'s, which stays for `Tadv` and the mesh columns (`celltoCellDist`, a
mean over the internal faces, and `Ncells` have no in-situ counterpart) and as
TwoPhaseFlow's file. Both agree to round-off: Eshape to 1e-15 relative (NeoFOAM's
`cutCellIso` and the kernels' sums against this repository's), Ebound bitwise, Emass at
1e-17 (another summation order).

* `discUniFlow`: numufoam's / the paper's setup (R = 0.2 at (0.25, 0.25), U = (1, 1),
  unit square, t = 0.5), E1 at t = 0.5 against numufoam's `error.csv`
  (`reference/numufoam.csv`). The default sweep is n10-n40 x CFL 0.1, 0.5 x
  Serial/CPU/GPU x isoAdvector/MULES (36 cases, ~1.5 min with `-c 1`); numufoam's finer
  meshes and CFLs are commented variants in `benchmark.yaml`. Only MULES has a numufoam
  counterpart (its normal is pointCellsLeastSquares, NeoN's Gauss linear: 0.84-1.05x
  numufoam's E1 at n10/n20, up to 3.5x at n320); numufoam's isoAlpha/plicRDF are other
  reconstructions than gradAlpha, so isoAdvector compares in trend only.
* `discUniFlowTestsuite`: TwoPhaseFlow's `test-discUniFlow` (R = 0.25, U = (1, 0.5),
  100 x 60, t = 4), against the stored TwoPhaseFlow advectorVoF runs
  (`reference/twophaseflow_*.csv`): MULES agrees to 1.7e-14, gradAlpha
  isoAdvector to 4.7e-9 relative (volTaylor plane search) on every executor.

### Parasitic currents: surfaceTension/staticDrop, acceleration/tiltedBox

Both run NeoFOAM's built-in `incompressibleVoFNeoN` through `incompressibleVoFNeoNSweep`
(`solvers/vof_neon.py`, the same spec and `run`, without the `--no-preprocess` option of
the sweep's `solve` rule, which `Foam::argList` rejects). The metrics are NeoFOAM
`postProcess` tables (`case/system/postProcess.yaml`), evaluated in-run at the field
write times; each benchmark's `metrics.py` derives the rest at collect (`derive`). The
maxima over time are sampled at the write times. The tables see the solver's fields in
full precision, the earlier field-based metrics the written ones (`writePrecision 12`):
the values agree to 2e-12 (staticDrop) and 2e-11 (tiltedBox) relative on Serial and CPU;
staticDrop's GPU runs to 1e-10, the run-to-run spread of the GPU solves.

**staticDrop** is NeoFOAM's `test/solver/incompressibleVoFNeoN/cases/stationaryDroplet`
(neither numufoam nor TwoPhaseFlow has a static drop with surface tension driving the
flow): a 2 mm water cylinder (setAlphaField) in air in an 8 mm box, open top, sigma 0.07,
g = 0, MULES, Brackbill CSF with gradAlpha curvature, `deltaT 2e-5` to t = 4e-3, written
every 10th step. Meshes n20, n40, n80 (R/dx = 5, 10, 20), all executors (9 cases, about
1 min with `-c 1`). Metrics: max/mean |U| over time (`mag | max`, the volume-weighted
mean `mag | volIntegrate` over `area | sum`), Ca = mu_water max|U| / sigma, the Laplace
jump `mean p_rgh(r < R/2) - mean p_rgh(r > 3R/2)` (`sphere`, `not sphere` with `mean`;
the nominal R = 2 mm selects the same cells as R of the water volume, 0.3 ... 1 % less)
against sigma/R (R of the water volume, `alpha1 | volIntegrate`) as NeoFOAM's test
measures it. n40 reproduces the test (jump 29.9007 Pa, 14.7 %
below sigma/R; end max|U| 0.19897 m/s), n80 interFoam's 9.6 %; Serial, CPU and GPU agree
to 1e-10.

**tiltedBox** is TwoPhaseFlow's `run/benchmark/acceleration/tiltedBox` (numufoam's with
rho 1000/1): the unit box tilted 30 degrees about y, water below z = 0.1345, g = (0 0
-9.81), sigma 0, adaptive time step (Co 0.2) to t = 0.1, written every 0.005. NeoFOAM
has no transformPoints tool: the blockMeshDict's vertices are the rotated ones (another
angle is a mesh variant with other vertices), and the plane initial condition is
`tools/set_alpha_plane.py` (a `neofoam.plugins` tool; NeoFOAM's setAlphaField has no
plane). Differences to TwoPhaseFlow: isoAdvector with gradAlpha (plicRDF), an open top
with `p_rgh` fixedValue 0 (a closed box with pRefCell; incompressibleVoFNeoN has no
pressure reference), no momentum predictor. Metrics: max/mean |U| over time, max|U| at
t = 0.01 (TwoPhaseFlow's `results.csv`), the largest and mean |p - p_hydrostatic| relative
to the hydrostatic range (this repository's `hydrostaticError` node with `max`, and with
`volIntegrate` over `area | sum`: the rotated mesh's cell volumes differ by 1e-6, so the
means are volume-weighted). n16, n32, n64 x executors: 9 cases, about 40 s.

### Single phase: singlePhase/cavity, singlePhase/pitzDaily

Both run NeoFOAM's built-in `incompressibleFluidNeoN` (NeoN executors) through
`incompressibleFluidNeoNSweep` (`solvers/fluid_neon.py`, without the sweep's
`--no-preprocess`, which `Foam::argList` rejects); each `metrics.py` evaluates the
solver log and the case's postProcess tables (cavity) or written fields (pitzDaily) per
case, and writes the final profiles, which collect gathers into `profiles.csv`.

**cavity** is the lid-driven cavity at Re = 100 (OpenFOAM's icoFoam cavity on the unit
square, U_lid 1, nu 0.01; the tutorial's 0.1 m square is Re = 10): PISO with 2 correctors,
Gauss linear, adaptive time step (Co 0.5) to t = 20 (steady). Metrics: the L2 / Linf error
of u on the vertical and v on the horizontal centreline against Ghia, Ghia & Shin (1982),
J. Comput. Phys. 48, 387-411, Tables I and II (`reference/ghia1982.csv`), the change of U
over the last 2 s, the largest |U|, wall time and time per step. NeoN has no line
sampling, so the centrelines come from `box | rows` tables: U of the cell columns (rows)
within 0.03 of x = 0.5 (y = 0.5), which hold the two next to the line up to n = 160, and
`metrics.py` interpolates the same profile as from all cells; the change of U is this
repository's `change` node, max|U| `mag | max`. The in-situ U is full precision against
the written `writePrecision 12` before: on Serial and CPU the errors agree to 1e-10
relative, dU (a difference of nearly equal values) to 3e-8; on the GPU to 6e-9 and
1e-5, the run-to-run spread of its iterative solves. Reference also: OpenFOAM-v2406 icoFoam on
the same case and meshes (fixed dt 0.001), evaluated by the same `metrics.py`, stored in
`reference/icofoam.csv`. n20, n40, n80 x executors: 9 cases, about 7 min with `-c 1`.

**pitzDaily** is NeoFOAM's `pitzDaily_steady` tutorial (OpenFOAM's simpleFoam pitzDaily
with plain SIMPLE and p 0.3 / U 0.7 relaxation), k-epsilon with wall functions, 1500
iterations (NeoN has no residualControl; the metrics report the first iteration that
meets the tutorial's tolerances). Metrics: the reattachment length (sign change of the
lower wall's near-wall Ux downstream of the step), the backflow and the Ux profiles at
x/h = 1, 3, 5, 7, residuals, wall time; from the log and the written fields, not
postProcess tables: NeoFOAM's `residuals` source reads the fvMesh's solverPerformanceDict,
which NeoN's Ginkgo solves never fill, and the reattachment length interpolates the
near-wall Ux at the lower wall's face centres, which the `patch` source cannot sample on
a NeoN field. Reference: OpenFOAM-v2406 simpleFoam on the same
case and meshes, evaluated by the same `metrics.py` and stored in
`reference/openfoam*.csv`, and the measured x_r/h = 7.0 of Pitz & Daily (1983). Meshes coarse (the tutorial's cells halved) and tutorial x executors:
6 cases, about 5 min with `-c 1`.
