"""OpenFOAM-v2406 icoFoam on the cavity's case and mesh variants: ``reference/icofoam.csv``.

    pixi run python benchmarks/singlePhase/cavity/openfoam_reference.py [WORKDIR]

Per ``mesh`` variant of ``benchmark.yaml``: copies ``case/`` to ``WORKDIR/<mesh>`` (default
``runs/cavity``), sets the cells, runs ``blockMesh`` and ``icoFoam`` with
``$OPENFOAM_BASHRC`` (default ``~/OpenFOAM/OpenFOAM-v2406/etc/bashrc``) sourced, and
evaluates the run with the benchmark's ``metrics.py``. icoFoam has no adaptive time step:
it runs the case's ``deltaT`` 0.001 to t = 20 on every mesh (20 000 steps, about 5 min in
all); the ``executor`` and ``turbulenceProperties`` entries are unused. Writes per mesh the
last row of the metrics table.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
BASHRC = os.environ.get("OPENFOAM_BASHRC", str(Path.home() / "OpenFOAM/OpenFOAM-v2406/etc/bashrc"))
COLUMNS = ["mesh", "u_L2", "u_Linf", "v_L2", "v_Linf", "dU", "steps", "wall_s"]


def main(workdir: Path) -> None:
    spec = importlib.util.spec_from_file_location("cavity_metrics", HERE / "metrics.py")
    assert spec is not None and spec.loader is not None
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    meshes = yaml.safe_load((HERE / "benchmark.yaml").read_text())["dimensions"]["mesh"]
    rows = []
    for mesh, payload in meshes.items():
        n = payload["block_mesh_dict_config"]["blocks"][0]["cells"]
        case = workdir / mesh
        shutil.rmtree(case, ignore_errors=True)
        shutil.copytree(HERE / "case", case)
        block_mesh_dict = case / "system" / "blockMeshDict"
        text = block_mesh_dict.read_text().replace("(20 20 1)", "({} {} {})".format(*n))
        block_mesh_dict.write_text(text)
        script = f"set +eu; source {BASHRC}; set -eu; blockMesh > log.blockMesh 2>&1; "
        subprocess.run(["bash", "-c", script + "icoFoam > log.solver 2>&1"], cwd=case, check=True)
        rows.append({"mesh": mesh, **metrics.metrics(case).iloc[-1].to_dict()})
        print(f"{mesh}: {rows[-1]}", flush=True)
    pd.DataFrame(rows)[COLUMNS].to_csv(HERE / "reference" / "icofoam.csv", index=False)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/cavity"))
