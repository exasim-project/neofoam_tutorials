#!/bin/bash
# Export a benchmark's NeoFOAM sweep and run its Snakemake workflow, with
# OpenFOAM-v2406 sourced (pybFoam): pixi run benchmark FOLDER [--smoke] [--method NAME] [-c N]
set -euo pipefail
# OpenFOAM's bashrc uses unset variables and returns non-zero
set +eu
# shellcheck disable=SC1090
source "$NEOFOAM_BASHRC" >/dev/null 2>&1
set -eu
exec python -m neofoam_verification.run "$@"
