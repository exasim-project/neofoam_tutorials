"""``pixi run benchmark FOLDER [--smoke] [--method NAME] [-c N]``: export and run a benchmark.

FOLDER holds ``benchmark.yaml`` (:mod:`.suite.benchmark`). Its NeoFOAM sweep is exported
to ``results/<category>/<name>/`` and run by one Snakemake command, printed first; that
command alone reproduces the run (with OpenFOAM-v2406 sourced, as ``scripts/benchmark.sh``
does). ``--smoke`` keeps the benchmark's ``smoke`` variants, ``--method NAME``
(repeatable) runs NAME instead of the method dimension's variants.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from .suite.benchmark import export, name

RESULTS = Path(__file__).resolve().parents[2] / "results"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pixi run benchmark")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--method", action="append", default=[])
    parser.add_argument("-c", "--cores", type=int, default=4)
    args = parser.parse_args(argv)
    if not (args.folder / "benchmark.yaml").is_file():
        parser.error(f"no benchmark.yaml in {args.folder}")
    snakefile = export(args.folder, RESULTS / name(args.folder), args.smoke, args.method)
    workdir = os.path.relpath(snakefile.parent)
    command = ["snakemake", "-s", f"{workdir}/Snakefile", "-d", workdir, "-c", str(args.cores)]
    print(" ".join(command), flush=True)
    return subprocess.run(command).returncode


if __name__ == "__main__":
    sys.exit(main())
