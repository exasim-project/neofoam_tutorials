"""The derived columns of collect (``collect.derive``): TwoPhaseFlow's Emass and Ebound.

From the case's ``postProcess`` tables (``case/system/postProcess.yaml``): ``Emass`` =
``|mass - mass0|`` (the water volume against the start time's), ``Ebound`` =
``|max(-alpha_min, alpha_max - 1)|``, as ``volumeFractionError`` (Eshape is a table).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from neofoam_tutorials.metrics import table_errors


def derive(history: pd.DataFrame, case: Path) -> pd.DataFrame:
    return table_errors(history)
