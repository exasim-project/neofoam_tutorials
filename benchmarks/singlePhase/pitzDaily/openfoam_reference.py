"""OpenFOAM-v2406 simpleFoam on pitzDaily's case and mesh variants: ``reference/openfoam*.csv``.

    pixi run python benchmarks/singlePhase/pitzDaily/openfoam_reference.py [WORKDIR]

Per ``mesh`` variant of ``benchmark.yaml``: copies ``case/`` to ``WORKDIR/<mesh>`` (default
``runs/pitzDaily``), sets the blocks' cells, runs ``blockMesh`` and ``simpleFoam`` with
``$OPENFOAM_BASHRC`` (default ``~/OpenFOAM/OpenFOAM-v2406/etc/bashrc``) sourced, and
evaluates the run with the benchmark's ``metrics.py`` (the same log and fields
evaluation as the NeoFOAM cases). The case is NeoFOAM's: plain SIMPLE, 1500 iterations,
no residualControl (simpleFoam runs them all), the ``executor`` key unused. Writes

* ``reference/openfoam.csv`` -- per mesh the last row of the metrics table;
* ``reference/openfoam_profiles.csv`` -- per mesh the final Ux profiles (``nCells``, ``x_h``,
  ``y``, ``Ux``).
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
BASHRC = os.environ.get("OPENFOAM_BASHRC", str(Path.home() / "OpenFOAM/OpenFOAM-v2406/etc/bashrc"))
COLUMNS = [
    "mesh",
    "nCells",
    "iterations",
    "x_r",
    "x_r_h",
    "Umin_xh1",
    "Umin_xh3",
    "Umin_xh5",
    "wall_s",
]
HEX_CELLS = re.compile(r"(hex \([^)]*\)\s*)\(\d+ \d+ \d+\)")


def set_cells(block_mesh_dict: Path, blocks: list[dict[str, list[int]]]) -> None:
    cells = iter(blocks)
    text = HEX_CELLS.sub(
        lambda m: m.group(1) + "({} {} {})".format(*next(cells)["cells"]),
        block_mesh_dict.read_text(),
    )
    block_mesh_dict.write_text(text)


def run(case: Path) -> None:
    script = f"set +eu; source {BASHRC}; set -eu; blockMesh > log.blockMesh 2>&1; "
    script += "simpleFoam > log.solver 2>&1"
    subprocess.run(["bash", "-c", script], cwd=case, check=True)


def main(workdir: Path) -> None:
    spec = importlib.util.spec_from_file_location("pitzdaily_metrics", HERE / "metrics.py")
    assert spec is not None and spec.loader is not None
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    meshes = yaml.safe_load((HERE / "benchmark.yaml").read_text())["dimensions"]["mesh"]
    rows, profiles = [], []
    for mesh, payload in meshes.items():
        case = workdir / mesh
        shutil.rmtree(case, ignore_errors=True)
        shutil.copytree(HERE / "case", case)
        set_cells(case / "system" / "blockMeshDict", payload["block_mesh_dict_config"]["blocks"])
        run(case)
        table = metrics.metrics(case)
        rows.append({"mesh": mesh, **table.iloc[-1].to_dict()})
        final = pd.read_csv(case / "postProcessing" / "profiles.csv")
        profiles.append(final.assign(mesh=mesh))
        print(f"{mesh}: {rows[-1]}", flush=True)
    pd.DataFrame(rows)[COLUMNS].to_csv(HERE / "reference" / "openfoam.csv", index=False)
    profiles_table = pd.concat(profiles)[["mesh", "nCells", "x_h", "y", "Ux"]]
    profiles_table.to_csv(
        HERE / "reference" / "openfoam_profiles.csv", index=False, float_format="%.6g"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/pitzDaily"))
