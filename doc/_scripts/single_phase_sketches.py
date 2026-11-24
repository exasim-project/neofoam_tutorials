"""The setup sketches of the single-phase benchmarks: ``doc/_static/setup/<name>.{png,svg}``.

``pixi run python doc/_scripts/single_phase_sketches.py`` draws each case's blocks (x-y,
from ``blockMeshDict``), its patches with their ``U`` and ``p`` boundary conditions, and
the key values, every number read from ``benchmarks/singlePhase/<name>/case/``. Commit
the images.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from foamlib import FoamFile  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks" / "singlePhase"
OUT = ROOT / "doc" / "_static" / "setup"
COLOURS = ("#54278f", "#238b45", "#cb181d", "#2171b5", "#d94801")
VELOCITY, BLOCK = "#238b45", "#c8c8c8"

plt.rcParams.update(
    {"font.size": 9, "svg.fonttype": "none", "svg.hashsalt": "setup", "font.family": "DejaVu Sans"}
)


class Case:
    def __init__(self, name: str) -> None:
        self.path = BENCHMARKS / name / "case"
        mesh = FoamFile(self.path / "system" / "blockMeshDict")
        self.scale = float(mesh["scale"])
        self.vertices = np.asarray(mesh["vertices"], dtype=float)[:, :2] * self.scale
        # the blocks' entries in a row: "hex", the 8 vertex labels, cells, grading ...
        entries = list(mesh["blocks"])
        self.blocks = [list(entries[i + 1])[:4] for i, e in enumerate(entries) if e == "hex"]
        self.boundary = [(n, e) for n, e in mesh["boundary"] if e["type"] != "empty"]

    def get(self, rel: str) -> Any:
        return FoamFile(self.path / rel)

    def bc(self, field: str, patch: str) -> str:
        entry = self.get(f"0/{field}")["boundaryField"][patch]
        value = entry.get("value")
        if entry["type"] == "fixedValue" and value is not None:
            shown = " ".join(f"{v:g}" for v in np.atleast_1d(value))
            return f"{field} = {shown}" if np.ndim(value) == 0 else f"{field} = ({shown})"
        return f"{field} {entry['type']}"


def draw_case(case: Case, ax: Axes, fields: tuple[str, ...], label_at: dict[str, Any]) -> None:
    for block in case.blocks:
        ax.add_patch(Polygon(case.vertices[block], fill=False, ec=BLOCK, lw=0.8, zorder=1))
    for i, (patch, entry) in enumerate(case.boundary):
        colour = COLOURS[i % len(COLOURS)]
        for face in entry["faces"]:
            points = np.unique(np.round(case.vertices[face], 12), axis=0)
            ax.plot(*points.T, color=colour, lw=2.5, zorder=3, solid_capstyle="butt")
        text = f"{patch} ({entry['type']})\n" + ", ".join(case.bc(f, patch) for f in fields)
        xy, align = label_at[patch]
        ax.text(*xy, text, color=colour, fontsize=8, **align)


def cavity(fig: plt.Figure, ax: Axes) -> list[str]:
    case = Case("cavity")
    centre = {"ha": "center", "va": "center"}
    draw_case(
        case,
        ax,
        ("U", "p"),
        {
            "movingWall": ((0.5, 1.12), centre),
            "fixedWalls": ((0.5, -0.12), centre),
        },
    )
    lid = float(case.get("0/U")["boundaryField"]["movingWall"]["value"][0])
    ax.annotate(
        "",
        xy=(0.75, 1.03),
        xytext=(0.25, 1.03),
        arrowprops={"arrowstyle": "-|>", "color": VELOCITY, "lw": 2},
    )
    ax.plot([0.5, 0.5], [0, 1], "k--", lw=0.8)
    ax.plot([0, 1], [0.5, 0.5], "k--", lw=0.8)
    ax.text(0.52, 0.05, "u(0.5, y)", fontsize=8)
    ax.text(0.03, 0.52, "v(x, 0.5)", fontsize=8)
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylim(-0.25, 1.25)
    nu = float(case.get("constant/transportProperties")["nu"])
    control = case.get("system/controlDict")
    side = float(np.ptp(case.vertices[:, 0]))
    return [
        f"unit square, side L = {side:g} m (one cell thick)",
        f"lid U = {lid:g} m/s, ν = {nu:g} m²/s",
        f"Re = U L / ν = {lid * side / nu:g}, laminar",
        "walls: no slip; p zeroGradient, pRefCell 0",
        "PISO, 2 correctors, Gauss linear",
        f"adaptive dt: maxCo = {float(control['maxCo']):g}",
        f"end time {float(control['endTime']):g} s (steady state)",
        "dashed: the centrelines compared",
        "  with Ghia et al. (1982)",
    ]


def pitz_daily(fig: plt.Figure, ax: Axes) -> list[str]:
    case = Case("pitzDaily")
    v = case.vertices
    h = float(v[3, 1] - v[2, 1])  # the step: the lower wall drops from y = 0 to -h at x = 0
    right = {"ha": "left", "va": "center"}
    draw_case(
        case,
        ax,
        ("U",),
        {
            "inlet": ((-0.022, 0.012), {"ha": "right", "va": "center"}),
            "outlet": ((0.293, 0.0), right),
            "upperWall": ((0.13, 0.033), {"ha": "center", "va": "bottom"}),
            "lowerWall": ((0.13, -0.034), {"ha": "center", "va": "top"}),
        },
    )
    u = float(case.get("0/U")["boundaryField"]["inlet"]["value"][0])
    ax.annotate(
        "",
        xy=(-0.004, 0.0127),
        xytext=(-0.019, 0.0127),
        arrowprops={"arrowstyle": "-|>", "color": VELOCITY, "lw": 2},
    )
    for n in (1, 3, 5, 7):
        ax.plot([n * h, n * h], [-h, h], "k--", lw=0.6)
        ax.text(n * h, h + 0.002, f"{n}h", ha="center", fontsize=7)
    ax.annotate("", xy=(0.004, -h), xytext=(0.004, 0), arrowprops={"arrowstyle": "<->", "lw": 0.8})
    ax.text(0.006, -h / 2, "h", va="center")
    ax.set_xlim(-0.11, 0.36)
    ax.set_ylim(-0.05, 0.05)
    nu = float(case.get("constant/transportProperties")["nu"])
    turbulence = case.get("constant/turbulenceProperties")["RAS"]["RASModel"]
    k = float(case.get("0/k")["boundaryField"]["inlet"]["value"])
    epsilon = float(case.get("0/epsilon")["boundaryField"]["inlet"]["value"])
    end = float(case.get("system/controlDict")["endTime"])
    return [
        f"step height h = {h * 1e3:g} mm",
        f"inlet U = {u:g} m/s, ν = {nu:g} m²/s",
        f"Re_h = U h / ν = {u * h / nu:.0f}",
        f"{turbulence}, wall functions",
        f"inlet k = {k:g}, ε = {epsilon:g}",
        "outlet: p = 0, U zeroGradient",
        f"SIMPLE, {end:g} iterations",
        "dashed: the profile stations x/h",
    ]


#: benchmark -> (draw, figure size)
SKETCHES: dict[str, tuple[Callable[[plt.Figure, Axes], list[str]], tuple[float, float]]] = {
    "cavity": (cavity, (8.5, 4.2)),
    "pitzDaily": (pitz_daily, (9.5, 2.8)),
}


def draw(name: str) -> None:
    function, size = SKETCHES[name]
    fig = plt.figure(figsize=size)
    ax = fig.add_axes((0.02, 0.06, 0.6, 0.88))
    info = function(fig, ax)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.64, 0.92, f"singlePhase/{name}", fontsize=11, weight="bold", va="top")
    fig.text(0.64, 0.80, "\n".join(info), va="top", linespacing=1.6)
    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / name
    fig.savefig(stem.with_suffix(".png"), dpi=110, metadata={"Software": None})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Date": None, "Creator": None})
    plt.close(fig)
    print(stem.with_suffix(".png").relative_to(ROOT))


if __name__ == "__main__":
    for name in sys.argv[1:] or SKETCHES:
        draw(name)
