"""The setup sketch of each benchmark: ``doc/_static/setup/<name>.{png,svg}``.

``pixi run python doc/_scripts/setup_sketches.py [NAME ...]`` draws the domain, the patches
with their boundary conditions, the coarsest mesh of ``benchmark.yaml`` as a grid, the
initial interface and the key values. Every number is read from the benchmark's ``case/``
(``blockMeshDict``, ``setAlphaFieldDict``, ``0/*``, ``constant/*``, ``controlDict``), so a
rerun after a case change keeps the sketch correct. Commit the images.

A new benchmark gets a sketch by a function ``(sketch, ax) -> info lines`` in
:data:`SKETCHES`; :class:`Sketch` draws the common parts.
"""

from __future__ import annotations

import math
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from foamlib import FoamFile  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon  # noqa: E402

from neofoam_tutorials.foam_random import centres  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks"
OUT = ROOT / "doc" / "_static" / "setup"
AXES = "xyz"

WATER, LINE, GRID = "#9ecae1", "#08519c", "#c8c8c8"
VELOCITY, GRAVITY, PATCH = "#238b45", "#cb181d", "#54278f"

plt.rcParams.update(
    {"font.size": 9, "svg.fonttype": "none", "svg.hashsalt": "setup", "font.family": "DejaVu Sans"}
)


def _foam(path: Path) -> Any:
    return FoamFile(path)


class Sketch:
    """A benchmark's case, projected on its two meshed directions."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.folder = BENCHMARKS / name
        self.case = self.folder / "case"
        mesh = _foam(self.case / "system" / "blockMeshDict")
        self.scale = float(mesh.get("scale", 1))
        self.vertices = np.asarray(mesh["vertices"], dtype=float) * self.scale
        self.boundary = list(mesh["boundary"])
        self.cells = self._coarsest()
        self.plane = [i for i, c in enumerate(self.cells) if c != 1]

    def _coarsest(self) -> list[int]:
        spec = yaml.safe_load((self.folder / "benchmark.yaml").read_text())
        meshes = [
            p["block_mesh_dict_config"]["blocks"][0]["cells"]
            for p in spec["dimensions"]["mesh"].values()
        ]
        return min(meshes, key=math.prod)

    def p(self, point: Any) -> np.ndarray:
        """A 3D point (case units) in the sketch plane."""
        return np.asarray(point, dtype=float)[self.plane]

    def dict(self, rel: str) -> Any:
        return _foam(self.case / rel)

    @property
    def label(self) -> tuple[str, str]:
        return AXES[self.plane[0]], AXES[self.plane[1]]

    # -- the common parts ----------------------------------------------------------------

    def outline(self) -> np.ndarray:
        pts = np.unique(np.round(self.vertices[:, self.plane], 12), axis=0)
        centre = pts.mean(axis=0)
        order = np.argsort(np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0]))
        return pts[order]

    def grid(self, ax: Axes) -> None:
        v = self.vertices[:, self.plane]
        directions = {0: v[1] - v[0], 1: v[3] - v[0], 2: v[4] - v[0]}
        (ia, a), (ib, b) = [(i, directions[i]) for i in range(3) if self.cells[i] != 1]
        na, nb = self.cells[ia], self.cells[ib]
        for i in range(na + 1):
            start = v[0] + i / na * a
            ax.plot(*zip(start, start + b), color=GRID, lw=0.5, zorder=1)
        for j in range(nb + 1):
            start = v[0] + j / nb * b
            ax.plot(*zip(start, start + a), color=GRID, lw=0.5, zorder=1)

    def domain(self, ax: Axes) -> None:
        ax.add_patch(Polygon(self.outline(), closed=True, fill=False, ec="black", lw=1.2, zorder=3))
        self.grid(ax)

    def _bcs(self, patch: str) -> list[str]:
        out = []
        for field in ("U", "p_rgh"):
            path = self.case / "0" / field
            if not path.exists():
                continue
            for key, value in _foam(path)["boundaryField"].items():
                if re.fullmatch(key.strip('"'), patch):
                    out.append(f"{field} {value['type']}")
                    break
        return out

    def patches(self, ax: Axes, pad: float, merge: bool = False) -> None:
        """Label every non-empty patch at its edges, outside the domain."""
        centre = self.outline().mean(axis=0)
        for patch, entry in self.boundary:
            if entry["type"] == "empty":
                continue
            bcs = self._bcs(patch)
            text = f"{patch} ({entry['type']})" + (f"\n{', '.join(bcs)}" if bcs else "")
            for k, face in enumerate(entry["faces"]):
                pts = np.unique(np.round(self.vertices[face][:, self.plane], 12), axis=0)
                mid = pts.mean(axis=0)
                d = pts[1] - pts[0]
                normal = np.array([d[1], -d[0]]) / np.linalg.norm(d)
                if np.dot(normal, mid - centre) < 0:
                    normal = -normal
                angle = math.degrees(math.atan2(d[1], d[0]))
                angle = (angle + 90) % 180 - 90
                ax.plot(*pts.T, color=PATCH, lw=2.5, zorder=4, solid_capstyle="butt")
                if merge and k > 0:
                    continue
                ax.text(
                    *(mid + pad * normal),
                    text,
                    rotation=angle,
                    color=PATCH,
                    ha="center",
                    va="center",
                    fontsize=8,
                    rotation_mode="anchor",
                )

    def phases(self) -> dict[str, Any]:
        tp = self.dict("constant/transportProperties")
        return {name: tp[name] for name in tp["phases"]} | {"sigma": tp["sigma"]}

    def control(self, key: str) -> Any:
        return self.dict("system/controlDict")[key]

    def grid_line(self) -> str:
        cells = [c for c in self.cells if c != 1]
        return f"grid: coarsest mesh, {' × '.join(map(str, cells))} cells"


def _arrow(ax: Axes, start: np.ndarray, vector: np.ndarray, color: str, text: str) -> None:
    ax.annotate(
        "",
        xy=start + vector,
        xytext=start,
        zorder=6,
        arrowprops={"arrowstyle": "-|>", "color": color, "lw": 2},
    )
    ax.text(*(start + vector * 1.08), text, color=color, ha="left", va="bottom", zorder=6)


def _disc(ax: Axes, centre: np.ndarray, radius: float, **kw: Any) -> None:
    ax.add_patch(Circle(centre, radius, zorder=2, **kw))


def _phase_line(phase: dict[str, Any], name: str) -> str:
    return f"{name}: ρ = {phase['rho']:g}, ν = {phase['nu']:g}"


# -- the benchmarks ---------------------------------------------------------------------


def circle(s: Sketch, ax: Axes) -> list[str]:
    alpha = s.dict("system/setAlphaFieldDict")
    origin, radius = np.asarray(alpha["origin"], dtype=float), float(alpha["radius"])
    tools = yaml.safe_load((s.case / "system" / "preprocess.yaml").read_text())["tools"]
    samples = next(t.get("samples", 1) for t in tools if t["tool"] == "setAlphaField")
    o = s.p(origin)
    _disc(ax, o, radius, fc=WATER, ec=LINE, lw=1.5, alpha=0.8)
    lo, hi = s.p(0.9 * origin), s.p(1.1 * origin)
    ax.add_patch(
        Polygon(
            [lo, (hi[0], lo[1]), hi, (lo[0], hi[1])],
            fill=False,
            ls="--",
            ec="black",
            lw=0.8,
            zorder=5,
        )
    )
    for c in centres(origin, samples):
        ax.plot(*s.p(c), "k.", ms=3, zorder=5)
    ax.annotate(
        "",
        xy=o + [radius, 0],
        xytext=o,
        zorder=6,
        arrowprops={"arrowstyle": "->", "color": "black"},
    )
    ax.text(o[0] + radius / 2, o[1] + 0.03, "R", ha="center", va="bottom")
    ext = s.outline().max(axis=0) - s.outline().min(axis=0)
    return [
        f"domain {ext[0]:g} × {ext[1]:g}",
        f"R = {radius:.8f}",
        f"centre o = ({o[0]:g}, {o[1]:g})",
        f"{samples} samples: centres drawn in",
        "  [0.9 o, 1.1 o] (dashed box, dots)",
        "no flow, no time stepping:",
        "  reconstruction only",
        s.grid_line(),
    ]


def _translated_disc(s: Sketch, ax: Axes) -> list[str]:
    alpha = s.dict("system/setAlphaFieldDict")
    start, radius = s.p(alpha["origin"]), float(alpha["radius"])
    u = s.p(s.dict("0/U")["internalField"])
    end_time = float(s.control("endTime"))
    end = start + u * end_time
    _disc(ax, start, radius, fc=WATER, ec=LINE, lw=1.5, alpha=0.8)
    _disc(ax, end, radius, fill=False, ec=LINE, lw=1.5, ls="--")
    ax.text(*start, "t = 0", ha="center", va="center", zorder=6)
    ax.text(*end, f"t = {end_time:g}", ha="center", va="center", zorder=6)
    ax.annotate(
        "",
        xy=end - u / np.linalg.norm(u) * radius,
        zorder=6,
        xytext=start + u / np.linalg.norm(u) * radius,
        arrowprops={"arrowstyle": "-|>", "color": VELOCITY, "lw": 2},
    )
    mid = (start + end) / 2
    ax.text(
        mid[0] + 0.04 * end_time * np.linalg.norm(u),
        mid[1],
        "  U t",
        color=VELOCITY,
        ha="left",
        va="top",
    )
    ext = s.outline().max(axis=0) - s.outline().min(axis=0)
    x, z = s.label
    return [
        f"domain {ext[0]:g} × {ext[1]:g} ({x}-{z})",
        f"R = {radius:g}, start ({start[0]:g}, {start[1]:g})",
        f"U = ({u[0]:g}, {u[1]:g}), uniform",
        f"end time {end_time:g}: end ({end[0]:g}, {end[1]:g})",
        f"maxAlphaCo = {float(s.control('maxAlphaCo')):g} (fixed dt)",
        s.grid_line(),
    ]


def static_drop(s: Sketch, ax: Axes) -> list[str]:
    alpha = s.dict("system/setAlphaFieldDict")
    centre, radius = s.p(alpha["origin"]), float(alpha["radius"])
    _disc(ax, centre, radius, fc=WATER, ec=LINE, lw=1.5, alpha=0.8)
    ax.annotate(
        "",
        xy=centre + [radius, 0],
        xytext=centre,
        zorder=6,
        arrowprops={"arrowstyle": "->", "color": "black"},
    )
    ax.text(centre[0] + radius / 2, centre[1] + radius * 0.05, "R", ha="center", va="bottom")
    ax.text(centre[0], centre[1] - radius * 0.4, "water", ha="center", color=LINE)
    ph = s.phases()
    g = s.dict("constant/g")["value"]
    ext = s.outline().max(axis=0) - s.outline().min(axis=0)
    dt, end = float(s.control("deltaT")), float(s.control("endTime"))
    return [
        f"domain {ext[0] * 1e3:g} × {ext[1] * 1e3:g} mm",
        f"R = {radius * 1e3:g} mm at the centre",
        f"σ = {ph['sigma']:g} N/m, g = ({' '.join(f'{c:g}' for c in g)})",
        _phase_line(ph["water"], "water"),
        _phase_line(ph["air"], "air"),
        f"σ/R = {ph['sigma'] / radius:g} Pa (Laplace jump)",
        f"dt = {dt:g} s fixed, {round(end / dt)} steps",
        f"end time {end:g} s",
        s.grid_line(),
    ]


def tilted_box(s: Sketch, ax: Axes) -> list[str]:
    alpha = s.dict("system/setAlphaFieldDict")
    level = float(alpha["origin"][2])
    box = s.outline()
    # the box below the interface z = level (water): clip the convex outline
    water = []
    for a, b in zip(box, np.roll(box, -1, axis=0)):
        if a[1] <= level:
            water.append(a)
        if (a[1] - level) * (b[1] - level) < 0:
            water.append(a + (level - a[1]) / (b[1] - a[1]) * (b - a))
    ax.add_patch(Polygon(water, closed=True, fc=WATER, ec="none", alpha=0.8, zorder=2))
    xs = [p[0] for p in water if abs(p[1] - level) < 1e-12]
    ax.plot([min(xs), max(xs)], [level, level], color=LINE, lw=1.5, zorder=3)
    ax.text(
        np.mean(xs),
        level + 0.02,
        f"interface z = {level:g}",
        color=LINE,
        ha="center",
        va="bottom",
        zorder=6,
    )
    ax.text(np.mean(xs), level - 0.12, "water", color=LINE, ha="center", zorder=6)
    v0, v1 = s.p(s.vertices[0]), s.p(s.vertices[1])
    angle = math.degrees(math.atan2(*(v1 - v0)[::-1]))
    ax.plot([v0[0], v0[0] + 0.45], [v0[1], v0[1]], "k--", lw=0.8)
    ax.add_patch(Arc(v0, 0.7, 0.7, theta1=angle, theta2=0, lw=1))
    ax.text(v0[0] + 0.37, v0[1] - 0.1, f"{abs(angle):.0f}°", va="center")
    g = s.p(s.dict("constant/g")["value"])
    top = box[:, 1].max()
    _arrow(ax, np.array([box[:, 0].max() - 0.05, top]), g / np.linalg.norm(g) * 0.25, GRAVITY, "")
    ax.text(box[:, 0].max() - 0.02, top - 0.12, f"g = {np.linalg.norm(g):g}", color=GRAVITY)
    ph = s.phases()
    edge = np.linalg.norm(v1 - v0)
    return [
        f"unit box (edge {edge:g}) tilted by {abs(angle):.0f}°",
        f"water below z = {level:g}, air above",
        f"g = (0 0 {-np.linalg.norm(g):g}), σ = {ph['sigma']:g}",
        _phase_line(ph["water"], "water"),
        _phase_line(ph["air"], "air"),
        f"adaptive dt: maxCo = {float(s.control('maxCo')):g}",
        f"end time {float(s.control('endTime')):g} s",
        s.grid_line(),
    ]


#: benchmark -> (draw, figure size, patch label offset, one label per patch)
SKETCHES: dict[
    str, tuple[Callable[[Sketch, Axes], list[str]], tuple[float, float], float, bool]
] = {
    "reconstruction/circle": (circle, (7.5, 4.0), 0.12, True),
    "advection/discUniFlow": (_translated_disc, (7.5, 4.0), 0.06, True),
    "advection/discUniFlowTestsuite": (_translated_disc, (8.5, 3.8), 0.3, True),
    "surfaceTension/staticDrop": (static_drop, (7.5, 4.0), 0.0007, False),
    "acceleration/tiltedBox": (tilted_box, (7.5, 4.6), 0.1, False),
}


def draw(name: str) -> None:
    function, size, pad, merge = SKETCHES[name]
    s = Sketch(name)
    fig = plt.figure(figsize=size)
    ax = fig.add_axes((0.02, 0.04, 0.6, 0.92))
    s.domain(ax)
    info = function(s, ax)
    s.patches(ax, pad, merge)
    ax.set_aspect("equal")
    ax.autoscale_view()
    lo, hi = s.outline().min(axis=0), s.outline().max(axis=0)
    margin = 2.6 * pad
    ax.set_xlim(lo[0] - margin, hi[0] + margin)
    ax.set_ylim(lo[1] - margin, hi[1] + margin)
    ax.axis("off")
    x, y = s.label
    ax.annotate(
        "",
        xy=(lo[0] - margin * 0.6 + 0.12 * (hi[0] - lo[0]), lo[1] - margin * 0.6),
        xytext=(lo[0] - margin * 0.6, lo[1] - margin * 0.6),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    ax.annotate(
        "",
        xy=(lo[0] - margin * 0.6, lo[1] - margin * 0.6 + 0.12 * (hi[1] - lo[1])),
        xytext=(lo[0] - margin * 0.6, lo[1] - margin * 0.6),
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    ax.text(lo[0] - margin * 0.6 + 0.13 * (hi[0] - lo[0]), lo[1] - margin * 0.6, x, va="center")
    ax.text(lo[0] - margin * 0.6, lo[1] - margin * 0.6 + 0.13 * (hi[1] - lo[1]), y, ha="center")
    fig.text(0.65, 0.92, name, fontsize=11, weight="bold", va="top")
    fig.text(0.65, 0.84, "\n".join(info), va="top", linespacing=1.6)
    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / Path(name).name
    fig.savefig(stem.with_suffix(".png"), dpi=110, metadata={"Software": None})
    fig.savefig(stem.with_suffix(".svg"), metadata={"Date": None, "Creator": None})
    plt.close(fig)
    print(stem.with_suffix(".png").relative_to(ROOT))


def main(names: list[str]) -> None:
    for name in names or SKETCHES:
        draw(name)


if __name__ == "__main__":
    main(sys.argv[1:])
