# neofoam_tutorials

Reproducible benchmarks that show the state of NeoFOAM's verification: classic
single- and multiphase cases (most from TwoPhaseFlow's benchmark suite) run with NeoFOAM
on NeoN's Serial, CPU and GPU executors, next to reference data from OpenFOAM,
TwoPhaseFlow, numufoam and the literature.

Why: a solver port is only trusted when anyone can rerun the same cases and see how close
it gets. The results are therefore shown, not judged; a run is only flagged when a result
changes drastically from the published snapshot.

**Results and documentation: https://exasim-project.com/neofoam_tutorials/**

## Benchmarks

| Benchmark | What it shows |
|---|---|
| [reconstruction/circle](https://exasim-project.com/neofoam_tutorials/multiphase/circle.html) | interface reconstruction of a circle (PLIC, gradAlpha) |
| [advection/discUniFlow](https://exasim-project.com/neofoam_tutorials/multiphase/disc_uni_flow.html) | advection of a disc in uniform flow, against numufoam |
| [advection/discUniFlowTestsuite](https://exasim-project.com/neofoam_tutorials/multiphase/disc_uni_flow_testsuite.html) | the same disc against TwoPhaseFlow's `advectorVoF` |
| [surfaceTension/staticDrop](https://exasim-project.com/neofoam_tutorials/multiphase/static_drop.html) | parasitic currents of a static drop |
| [acceleration/tiltedBox](https://exasim-project.com/neofoam_tutorials/multiphase/tilted_box.html) | hydrostatic balance in a tilted box |
| [freeSurface/damBreak](https://exasim-project.com/neofoam_tutorials/multiphase/dam_break.html) | collapsing water column, against Martin & Moyce and interFoam |
| [singlePhase/cavity](https://exasim-project.com/neofoam_tutorials/single_phase/cavity.html) | laminar lid-driven cavity, against Ghia et al. and icoFoam |
| [singlePhase/pitzDaily](https://exasim-project.com/neofoam_tutorials/single_phase/pitz_daily.html) | turbulent backward-facing step, against simpleFoam |

## Use

Requires [pixi](https://pixi.sh), OpenFOAM-v2406 (for NeoFOAM's pybFoam) and a NeoFOAM
checkout; a GPU is optional.

```bash
pixi install
pixi run install-neofoam [NEOFOAM_CHECKOUT]   # builds NeoFOAM into the environment
pixi run benchmark benchmarks/singlePhase/cavity --smoke
pixi run test                                 # unit tests, no NeoFOAM run needed
pixi run docs                                 # builds the documentation
```

Details: [Install](https://exasim-project.com/neofoam_tutorials/getting_started.html#install),
[Run benchmarks](https://exasim-project.com/neofoam_tutorials/getting_started.html#run-benchmarks).

## Extend

- [Add a benchmark](https://exasim-project.com/neofoam_tutorials/getting_started.html#add-a-benchmark):
  a folder `benchmarks/<category>/<name>/` with `benchmark.yaml` and the case.
- [Test a new method](https://exasim-project.com/neofoam_tutorials/getting_started.html#test-a-new-method)
  on an existing benchmark with `--method`.
- [Refresh the published results](https://exasim-project.com/neofoam_tutorials/getting_started.html#refresh-the-results-in-this-documentation)
  after a full run.

## Layout

```
benchmarks/<category>/<name>/   benchmark.yaml, case/, plots.py, reference/*.csv
src/neofoam_tutorials/          the suite (sweep, collect, change flag, plots) and NeoFOAM plugins
test/                           unit tests of src/
doc/                            the documentation and its results snapshot (_generated/)
```

Conventions for contributors (and Claude Code) are in `.claude/rules/`.
