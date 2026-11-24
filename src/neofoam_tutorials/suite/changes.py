"""Drastic changes of a benchmark run against the documentation's snapshot.

The benchmarks showcase NeoFOAM's results; they do not judge them. :func:`compare` only
flags what moved a lot since the snapshot in ``doc/_generated/<category>/<name>/``: a
metric that changed by more than a factor :data:`FACTOR`, and a case that went missing
or whose metric became NaN. A case that is new in the run is reported, not flagged. The
workflow writes the result to ``changes.json`` and never fails on it.

Example::

    changes = compare(new_results, snapshot_results, keys=["executor", "mesh"])
    flagged = [c for c in changes if c["kind"] in FLAGGED]
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import pandas as pd

#: a metric is flagged if new / old leaves [1 / FACTOR, FACTOR]
FACTOR = 2.0
#: the kinds of change that are flagged; ``new`` (a case only in the run) is not
FLAGGED = ("ratio", "nan", "missing")

Change = dict[str, Any]


def _value(value: Any) -> float | None:
    return None if pd.isna(value) else float(value)


def _change(case: str, column: str, kind: str, old: Any = None, new: Any = None) -> Change:
    return {"case": case, "column": column, "kind": kind, "old": _value(old), "new": _value(new)}


def _metric_change(case: str, column: str, old: float, new: float) -> Change | None:
    if math.isnan(old):
        return None
    if math.isnan(new):
        return _change(case, column, "nan", old, new)
    if old == new:
        return None
    ratio = new / old if old != 0 else math.inf
    if 1 / FACTOR <= ratio <= FACTOR:
        return None
    return _change(case, column, "ratio", old, new)


def compare(new: pd.DataFrame, old: pd.DataFrame, keys: Sequence[str]) -> list[Change]:
    """The drastic changes of ``new`` against ``old``, their rows matched on ``keys``.

    Every numeric column of ``old`` but the keys is a metric (a column missing in ``new``
    counts as NaN). One entry ``{case, column, kind, old, new}`` per finding, ``kind``
    ``ratio``, ``nan``, ``missing`` (``old``'s case is not in ``new``) or ``new`` (the
    case is only in ``new``); ``column`` is empty for a whole case.
    """
    metrics = [c for c in old.select_dtypes("number").columns if c not in keys]
    old = old.rename(columns={c: f"{c}_old" for c in old.columns if c not in keys})
    new = new.rename(columns={c: f"{c}_new" for c in new.columns if c not in keys})
    pairs = old.merge(new, on=list(keys), how="outer", indicator=True)
    out = []
    for _, row in pairs.iterrows():
        if row["_merge"] == "left_only":
            out.append(_change(row["case_old"], "", "missing"))
            continue
        if row["_merge"] == "right_only":
            out.append(_change(row["case_new"], "", "new"))
            continue
        for column in metrics:
            new_value = row.get(f"{column}_new", math.nan)
            change = _metric_change(
                row["case_new"], column, float(row[f"{column}_old"]), float(new_value)
            )
            if change is not None:
                out.append(change)
    return out
