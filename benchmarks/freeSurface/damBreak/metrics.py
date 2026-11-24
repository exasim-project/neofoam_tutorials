"""The dam break's derived columns (``collect.derive``), per time step.

From the case's ``postProcess`` tables (``case/system/postProcess.yaml``: ``front`` --
the largest x of the bottom cells' centres with alpha > 0.5, every step; ``water`` --
``sum alpha V`` at the field write times) and the case's files:

* ``Z``, ``T`` -- Martin & Moyce's non-dimensional front ``x/a`` and time
  ``n t sqrt(g/a)``, ``a`` the column's width and ``n^2 a`` its height
  (``system/setFields.yaml``'s box), ``g`` of ``constant/g``;
* ``deltaT``, ``steps`` -- the time step and the number of steps so far;
* ``T_Z189`` -- ``T`` when the front first reaches Z = 1.89, Martin & Moyce's last
  point before the obstacle (NaN before);
* ``water_change`` -- the water volume relative to the first written one, minus 1.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from foamlib import FoamFile

Z_LAST_BEFORE_OBSTACLE = 1.89


def derive(history: pd.DataFrame, case: Path) -> pd.DataFrame:
    setfields = yaml.safe_load((case / "system" / "setFields.yaml").read_text())
    width, height, _ = setfields["regions"][0]["region"]["max"]
    g = float(np.linalg.norm(FoamFile(case / "constant" / "g")["value"]))

    time = history["Time"].to_numpy()
    table = history.assign(
        Z=history["front"] / width,
        T=time * np.sqrt(g * height) / width,
        deltaT=np.diff(time, prepend=0.0),
        steps=np.cumsum(time > 0),
        water_change=history["water"] / history["water"].dropna().iloc[0] - 1.0,
    )
    reached = table["T"].where(table["Z"] >= Z_LAST_BEFORE_OBSTACLE)
    table["T_Z189"] = reached.cummin().ffill()
    return table
