"""Render the temperature of the last written time and plot the plates' Nusselt numbers."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

RAYLEIGH = 1e11
HEIGHT = 1.0
T_HOT = 300.5
T_COLD = 299.5
CASE = Path(__file__).parent


def _reader() -> pv.POpenFOAMReader:
    """An OpenFOAM reader of the case's written times, cell data only."""
    foam_file = CASE / "case.foam"
    foam_file.touch()
    reader = pv.POpenFOAMReader(foam_file)
    reader.enable_all_cell_arrays()
    reader.cell_to_point_creation = False
    return reader


def _internal_mesh(reader: pv.POpenFOAMReader, time: float) -> pv.UnstructuredGrid:
    """The cells and their fields at ``time``."""
    reader.set_active_time_value(time)
    return reader.read()["internalMesh"]


def _nusselt(mesh: pv.UnstructuredGrid) -> tuple[float, float]:
    """The floor's and ceiling's Nusselt numbers from the wall-adjacent cells' temperature."""
    temperature = np.asarray(mesh.cell_data["T"])
    y = mesh.cell_centers().points[:, 1]
    floor = np.isclose(y, y.min())
    ceiling = np.isclose(y, y.max())
    delta_t = T_HOT - T_COLD
    nu_floor = np.mean((T_HOT - temperature[floor]) / y[floor]) * HEIGHT / delta_t
    nu_ceiling = np.mean((temperature[ceiling] - T_COLD) / (HEIGHT - y[ceiling])) * HEIGHT / delta_t
    return float(nu_floor), float(nu_ceiling)


def _render_temperature(mesh: pv.UnstructuredGrid, time: float) -> None:
    """The temperature field with its plumes, ``plots/temperature.png``."""
    plotter = pv.Plotter(off_screen=True, window_size=(1000, 900))
    plotter.add_mesh(
        mesh,
        scalars="T",
        cmap="RdBu_r",
        clim=(T_COLD, T_HOT),
        lighting=False,
        scalar_bar_args={"title": "T [K]", "vertical": True, "fmt": "%.2f"},
    )
    plotter.add_text(f"Ra = 1e11, Pr = 1: T at t = {time:g} s", font_size=12)
    plotter.view_xy()
    plotter.camera.zoom(1.1)
    plotter.screenshot(CASE / "plots" / "temperature.png")
    plotter.close()


def _plot_nusselt(times: list[float], nusselt: np.ndarray) -> None:
    """The plates' Nusselt numbers over time next to Niemela et al.'s fit, ``plots/nusselt.png``."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(times, nusselt[:, 0], marker=".", label="floor (hot)")
    ax.plot(times, nusselt[:, 1], marker=".", label="ceiling (cold)")
    ax.axhline(
        0.124 * RAYLEIGH**0.309, color="k", ls="--", label="0.124 Ra^0.309 (Niemela et al. 2000)"
    )
    ax.set_xlabel("t [s]")
    ax.set_ylabel("Nu")
    ax.legend()
    fig.savefig(CASE / "plots" / "nusselt.png", dpi=150, bbox_inches="tight")


def main() -> None:
    """Write the temperature and Nusselt plots and print the last Nusselt numbers."""
    reader = _reader()
    times = [time for time in reader.time_values if time > 0]
    meshes = [_internal_mesh(reader, time) for time in times]
    nusselt = np.array([_nusselt(mesh) for mesh in meshes])
    (CASE / "plots").mkdir(exist_ok=True)
    _render_temperature(meshes[-1], times[-1])
    _plot_nusselt(times, nusselt)
    print(f"t = {times[-1]:g} s: Nu floor {nusselt[-1, 0]:.1f}, ceiling {nusselt[-1, 1]:.1f}")


if __name__ == "__main__":
    main()
