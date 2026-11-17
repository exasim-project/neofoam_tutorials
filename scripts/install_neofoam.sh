#!/bin/bash
# Build and install NeoFOAM into the pixi environment (non-editable, as NeoFOAM's own
# build: Kokkos with OpenMP (NeoN_WITH_OMP=ON, NeoN_WITH_THREADS=OFF) and CUDA when nvcc
# is found, Ginkgo, pybFoam against OpenFOAM-v2406).
#
#   pixi run install-neofoam [NEOFOAM_CHECKOUT]     # default $NEOFOAM_SRC
#
# The toolchain is the system's (gcc via ccache, /usr/local/cuda), the one OpenFOAM-v2406
# is built with; cmake, ninja, scikit-build-core and nanobind come from the pixi env.
# The build directory is .pixi/build/neofoam, not the checkout's _skbuild (its own .venv
# build). 4 jobs, serialized with other NeoFOAM builds by build.lock.
set -euo pipefail
src=$(realpath "${1:-$NEOFOAM_SRC}")
build_dir="$PIXI_PROJECT_ROOT/.pixi/build/neofoam"
lock=${NEOFOAM_BUILD_LOCK:-$HOME/libsAndApps/NeoFOAM/.claude/worktrees/vof_scratch/plic_bench/build.lock}
log="$build_dir.log"
mkdir -p "$(dirname "$build_dir")"

set +u
# shellcheck disable=SC1090
source "$NEOFOAM_BASHRC" >/dev/null 2>&1
set -u
export CMAKE_BUILD_PARALLEL_LEVEL=4
export CCACHE_BASEDIR=${CCACHE_BASEDIR:-$(dirname "$src")}
if [ -d /usr/lib/ccache ]; then export PATH="/usr/lib/ccache:$PATH"; fi

echo "building NeoFOAM from $src into $CONDA_PREFIX (log: $log)"
flock "$lock" pip install "$src" -v --no-build-isolation --no-deps \
    -C build-dir="$build_dir" \
    -C cmake.define.NeoN_WITH_OMP=ON -C cmake.define.NeoN_WITH_THREADS=OFF \
    > "$log" 2>&1
python -c "import neofoam, pybFoam; from neofoam import neofoam_bindings; assert neofoam_bindings is not None"
echo "neofoam installed: $(python -c 'import neofoam; print(neofoam.__file__)')"
