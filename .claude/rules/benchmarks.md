---
paths:
  - "benchmarks/**"
---

# Benchmark rules

## Folder

- One benchmark = `benchmarks/<category>/<name>/` with `benchmark.yaml`, `case/`,
  `plots.py`, `reference/` (CSV only), optional `metrics.py` and its `test_metrics.py`.
- Repeat a published benchmark (TwoPhaseFlow, numufoam, literature): same geometry,
  parameters and error definitions; cite the source and commit/table at the top of
  `benchmark.yaml`.
- Reference numbers of other codes or papers are committed CSVs in `reference/`, never
  regenerated here; the CSV's source goes in its header comment or `benchmark.yaml`.

## benchmark.yaml

- Header comment: physics, case, what is swept, where each reference comes from.
- `dimensions` in NeoFOAM's `params.yaml` shape; always an executor dimension
  (Serial/CPU/GPU) and a `smoke` subset that runs in under a minute.
- No pass/fail checks: results are shown, and the change flag against the docs snapshot
  is the only automatic judgement.

## Metrics and plots

- Prefer in-situ postProcess tables; `metrics.py` only for what they cannot compute.
- Timing columns end in `_s` (the change flag skips them).
- `plots.py` uses `suite/plots.py` helpers; no hard-coded paths.

## Done

`pixi run benchmark <folder> --smoke` runs, and the docs page exists (see the docs rule).
