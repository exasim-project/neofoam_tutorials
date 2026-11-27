"""Plot the temperature of the last written time and the plates' Nusselt numbers over time."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from foamlib import FoamCase, FoamFieldFile

RAYLEIGH = 1e11
HEIGHT = 1.0
T_HOT = 300.5
T_COLD = 299.5
CASE = Path(__file__).parent


def _cell_centres() -> np.ndarray:
    """The cell centres that ``postProcess -func writeCellCentres -time 0`` wrote."""
    return np.asarray(FoamFieldFile(CASE / "0" / "C").internal_field)


def _nusselt(temperature: np.ndarray, centres: np.ndarray) -> tuple[float, float]:
    """The floor's and ceiling's Nusselt numbers from the wall-adjacent cells' temperature."""
    y = centres[:, 1]
    floor = np.isclose(y, y.min())
    ceiling = np.isclose(y, y.max())
    delta_t = T_HOT - T_COLD
    nu_floor = np.mean((T_HOT - temperature[floor]) / y[floor]) * HEIGHT / delta_t
    nu_ceiling = np.mean((temperature[ceiling] - T_COLD) / (HEIGHT - y[ceiling])) * HEIGHT / delta_t
    return float(nu_floor), float(nu_ceiling)


def _plot_temperature(temperature: np.ndarray, centres: np.ndarray, time: float) -> None:
    """The temperature field with its plumes, ``plots/temperature.png``."""
    fig, ax = plt.subplots(figsize=(6, 5.4))
    contour = ax.tricontourf(
        centres[:, 0], centres[:, 1], temperature, levels=64, cmap="RdBu_r", vmin=T_COLD, vmax=T_HOT
    )
    fig.colorbar(contour, ax=ax, label="T [K]")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"Ra = 1e11, Pr = 1: T at t = {time:g} s")
    fig.savefig(CASE / "plots" / "temperature.png", dpi=150, bbox_inches="tight")


def _plot_nusselt(times: list[float], nusselt: np.ndarray) -> None:
    """The plates' Nusselt numbers over time next to Niemela et al.'s fit, ``plots/nusselt.png``."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(times, nusselt[:, 0], label="floor (hot)")
    ax.plot(times, nusselt[:, 1], label="ceiling (cold)")
    ax.axhline(
        0.124 * RAYLEIGH**0.309, color="k", ls="--", label="0.124 Ra^0.309 (Niemela et al. 2000)"
    )
    ax.set_xlabel("t [s]")
    ax.set_ylabel("Nu")
    ax.legend()
    fig.savefig(CASE / "plots" / "nusselt.png", dpi=150, bbox_inches="tight")


def main() -> None:
    """Write the temperature and Nusselt plots and print the last Nusselt numbers."""
    centres = _cell_centres()
    written = [time for time in FoamCase(CASE) if time.time > 0]
    times = [time.time for time in written]
    nusselt = np.array(
        [_nusselt(np.asarray(time["T"].internal_field), centres) for time in written]
    )
    (CASE / "plots").mkdir(exist_ok=True)
    _plot_temperature(np.asarray(written[-1]["T"].internal_field), centres, times[-1])
    _plot_nusselt(times, nusselt)
    print(f"t = {times[-1]:g} s: Nu floor {nusselt[-1, 0]:.1f}, ceiling {nusselt[-1, 1]:.1f}")


if __name__ == "__main__":
    main()
