---
paths:
  - "benchmarks/**"
---

# Benchmark rules

A benchmark is a reproducible NeoFOAM run that anyone can repeat from pixi and that
shows the current state of the verification.

## Reproducible from pixi

- `pixi run benchmark benchmarks/<category>/<name>` runs it end to end, and `--smoke`
  runs a small subset of it; no manual steps, no machine-specific paths.
- Everything the run needs is in the benchmark folder (`benchmark.yaml`, `case/`) or the
  pixi environment.
- Reference data from other codes or papers is committed in `reference/` (CSV) with
  its source noted; it is shown next to the results, not used to pass or fail them.

## Outputs come from the solver

- The solver writes the outputs during the run through NeoFOAM's postprocessing
  (`case/system/postProcess.yaml`).
- When postprocessing cannot compute something yet, prefer adding a reusable member
  (NeoFOAM, or this package's `postprocess/`) over a script for one benchmark.

## Gathering and plots use the standard patterns

- Collecting results uses the suite's `collect` spec in `benchmark.yaml`; plots use the
  helpers in `suite/plots.py` (or NeoFOAM's), so benchmarks look and work alike.
- A pattern that more than one benchmark needs belongs in the suite, not copied between
  benchmarks.

## benchmark.yaml

- Start with a short comment: what is simulated, what is swept, and where any reference
  data comes from.
