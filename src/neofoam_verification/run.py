"""``pixi run benchmark FOLDER [--smoke] [--method NAME] [-c N]``: export and run benchmarks.

Every ``benchmark.yaml`` under FOLDER (:mod:`.suite.benchmark`) is run: its NeoFOAM
sweep is exported to ``results/<category>/<name>/`` and run by one Snakemake command,
printed first; that command alone reproduces the run (with OpenFOAM-v2406 sourced, as
``scripts/benchmark.sh`` does). ``--smoke`` keeps the benchmark's ``smoke`` variants,
``--method NAME`` (repeatable) runs NAME instead of the method dimension's variants.
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
    folders = sorted(p.parent for p in args.folder.rglob("benchmark.yaml"))
    if not folders:
        parser.error(f"no benchmark.yaml under {args.folder}")
    failed = []
    for folder in folders:
        snakefile = export(folder, RESULTS / name(folder), args.smoke, args.method)
        workdir = os.path.relpath(snakefile.parent)
        command = ["snakemake", "-s", f"{workdir}/Snakefile", "-d", workdir, "-c", str(args.cores)]
        print(" ".join(command), flush=True)
        if subprocess.run(command).returncode != 0:
            failed.append(name(folder))
    if failed:
        print(f"failed: {', '.join(failed)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
