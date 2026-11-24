---
paths:
  - "doc/**"
---

# Docs rules

Each benchmark has one page in `doc/<section>/<name>.rst`, listed in its section index:

- **Why and what is tested**: what the benchmark shows about NeoFOAM, and why it matters.
- **Case**: as brief as possible. Use an image when it helps explain the setup, preferably
  a visualization from the run's results; a sketch only when the results can't show it.
- **Parameter changes**: as a table (`_generated/<benchmark>/params.rst`).
- **Results**: show them (plots and tables from `_generated/`) and explain what they show.

## Build

- `sphinx-build -W` must pass, and the build must leave `doc/_generated` unchanged.
- Refresh the snapshot only from a full run (`pixi run docs` after `pixi run benchmark`),
  in its own commit.
