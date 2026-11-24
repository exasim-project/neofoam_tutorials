# CLAUDE.md — neofoam_tutorials

Verification benchmarks of NeoFOAM against OpenFOAM; see [README.md](README.md) for
the environment (`pixi install`), the tasks and the layout.

## Conventions

Path-scoped rules, loaded when Claude works on matching files:

- **[`.claude/rules/code-style.md`](.claude/rules/code-style.md)**: `src/`, `benchmarks/`, `doc/_scripts/`
- **[`.claude/rules/test-style.md`](.claude/rules/test-style.md)**: `tests/`

Never delete or weaken an existing test to get green — surface the conflict instead.
