"""The benchmark outputs in the documentation: ``doc/_generated/<category>/<name>/``.

``python doc/_scripts/sync_results.py`` (part of ``pixi run docs``) copies each
benchmark's ``results.csv``, ``checks.json`` and ``plots/*.png`` (shrunk to at most
:data:`MAX_WIDTH` pixels, 256 colours) from ``results/`` when a run exists there, then
renders the tables. ``conf.py`` calls :func:`render_all` only, so the committed snapshot
builds without ``results/``. Per benchmark it writes the include files

* ``results.rst`` -- the report's columns of ``results.csv`` (the group columns, the mesh,
  then ``benchmark.yaml``'s ``report``), with a note when the snapshot holds a subset of
  the full sweep (a ``--smoke`` run);
* ``checks.rst`` -- every check of ``checks.json`` with its status and detail;
* ``plots.rst`` -- one figure per plot.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image

from neofoam_verification.suite.benchmark import load
from neofoam_verification.suite.workflow import groups, mesh_column

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks"
RESULTS = ROOT / "results"
GENERATED = ROOT / "doc" / "_generated"
MAX_WIDTH = 900


def names() -> list[str]:
    """``<category>/<name>`` of every benchmark."""
    return sorted(
        p.parent.relative_to(BENCHMARKS).as_posix() for p in BENCHMARKS.rglob("benchmark.yaml")
    )


def shrink(src: Path, dst: Path) -> None:
    with Image.open(src) as image:
        image = image.convert("RGB")
        if image.width > MAX_WIDTH:
            height = round(image.height * MAX_WIDTH / image.width)
            image = image.resize((MAX_WIDTH, height), Image.Resampling.LANCZOS)
        image.quantize(colors=256).save(dst, optimize=True)


def copy(name: str) -> bool:
    """Replace the snapshot of ``name`` by its run in ``results/``, if there is one."""
    src, dst = RESULTS / name, GENERATED / name
    if not (src / "results.csv").exists() or not (src / "checks.json").exists():
        return False
    shutil.rmtree(dst, ignore_errors=True)
    (dst / "plots").mkdir(parents=True)
    for file in ("results.csv", "checks.json"):
        shutil.copy2(src / file, dst / file)
    for png in sorted((src / "plots").glob("*.png")):
        shrink(png, dst / "plots" / png.name)
    return True


def _cell(value: object) -> str:
    if isinstance(value, float):
        return "" if math.isnan(value) else f"{value:.4g}"
    return str(value)


def _list_table(header: list[str], rows: list[list[str]], widths: str = "auto") -> list[str]:
    lines = [".. list-table::", "   :header-rows: 1", f"   :widths: {widths}", ""]
    for row in [header, *rows]:
        lines += [f"   * - {row[0]}", *(f"     - {cell}" for cell in row[1:])]
    return [*lines, ""]


def render(name: str) -> None:
    folder, out = BENCHMARKS / name, GENERATED / name
    spec = load(folder)
    results = pd.read_csv(out / "results.csv")
    columns = [*groups(folder), mesh_column(folder), *spec.get("report", [])]
    full = math.prod(len(variants) for variants in spec["dimensions"].values())
    lines = []
    if len(results) < full:
        lines += [
            ".. note::",
            "",
            f"   This snapshot holds {len(results)} of the {full} cases of the full sweep "
            "(a ``--smoke`` run). Run the full sweep and refresh the snapshot "
            "(:ref:`refresh-the-results`) for all of them.",
            "",
        ]
    rows = [[_cell(v) for v in row] for row in results[columns].itertuples(index=False)]
    lines += _list_table([f"``{c}``" for c in columns], rows)
    (out / "results.rst").write_text("\n".join(lines))

    checks = json.loads((out / "checks.json").read_text())["checks"]
    count = {s: sum(c["status"] == s for c in checks) for s in ("pass", "fail", "skip")}
    lines = [f"{count['pass']} passed, {count['fail']} failed, {count['skip']} skipped.", ""]
    rows = [[c["check"], c["group"], f"**{c['status'].upper()}**", c["detail"]] for c in checks]
    lines += _list_table(["check", "group", "result", "detail"], rows, "30 15 10 45")
    (out / "checks.rst").write_text("\n".join(lines))

    lines = []
    for png in sorted((out / "plots").glob("*.png")):
        lines += [f".. figure:: /_generated/{name}/plots/{png.name}", f"   :alt: {png.stem}", ""]
        lines += [f"   ``{png.stem}``", ""]
    (out / "plots.rst").write_text("\n".join(lines))


def render_all() -> None:
    for name in names():
        if (GENERATED / name / "results.csv").exists():
            render(name)


def main() -> None:
    for name in names():
        print(f"{name}: {'copied' if copy(name) else 'kept the snapshot'}")
    render_all()


if __name__ == "__main__":
    main()
