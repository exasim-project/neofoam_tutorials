"""The declarative checks of ``benchmark.yaml`` on ``results.csv``.

Each check is evaluated per group of cases (the columns of the dimensions but the mesh:
executor and method) and gives one result ``{check, group, status, detail}``, status
``pass``, ``fail`` or ``skip`` (nothing to compare):

* ``{type: reference, file, match, columns, rtol}`` -- the stored table ``reference/<file>``,
  its rows matched to the results' by the ``match`` columns, every ``columns`` value to
  ``rtol`` relative;
* ``{type: order, column, spacing, minimum}`` -- the observed order, the least-squares
  slope of ``log(column)`` over ``log(spacing)`` across the group's resolutions, at least
  ``minimum``;
* ``{type: maximum, column, maximum}`` -- the group's largest ``column`` value at most
  ``maximum`` (a mass or bound error).

A check with ``where: {column: [values]}`` sees only the results' rows with those values.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

Check = dict[str, Any]


def _result(check: str, group: str, status: str, detail: str) -> Check:
    return {"check": check, "group": group, "status": status, "detail": detail}


def reference(check: Check, results: pd.DataFrame, folder: Path, by: Sequence[str]) -> list[Check]:
    on, columns = list(check["match"]), list(check["columns"])
    stored = pd.read_csv(folder / check["file"])
    stored = stored.astype({c: results[c].dtype for c in on})
    label = f"reference {check['file']}"
    out = []
    for key, rows in results.groupby(list(by)):
        group = " ".join(map(str, key))
        pairs = rows.merge(stored, on=on, suffixes=("", "_ref"))
        if pairs.empty:
            out.append(_result(label, group, "skip", "no stored row for these cases"))
            continue
        worst, where = 0.0, ""
        for column in columns:
            expected = pairs[column if column in on else f"{column}_ref"].to_numpy(float)
            diff = np.abs(pairs[column].to_numpy(float) - expected)
            diff /= np.maximum(np.abs(expected), np.finfo(float).tiny)
            i = int(np.argmax(diff))
            if diff[i] >= worst:
                worst, where = float(diff[i]), f"{column} {pairs['case'].iloc[i]}"
        status = "pass" if worst <= check["rtol"] else "fail"
        detail = f"max rel diff {worst:.1e} ({where}), rtol {check['rtol']:g}, {len(pairs)} cases"
        out.append(_result(label, group, status, detail))
    return out


def order(check: Check, results: pd.DataFrame, by: Sequence[str]) -> list[Check]:
    label = f"order {check['column']}"
    out = []
    for key, rows in results.groupby(list(by)):
        group = " ".join(map(str, key))
        if len(rows) < 2:
            out.append(_result(label, group, "skip", "one resolution"))
            continue
        fitted = fitted_order(rows[check["spacing"]], rows[check["column"]])
        status = "pass" if fitted >= check["minimum"] else "fail"
        out.append(_result(label, group, status, f"{fitted:.2f} (>= {check['minimum']:g})"))
    return out


def maximum(check: Check, results: pd.DataFrame, by: Sequence[str]) -> list[Check]:
    label = f"maximum {check['column']}"
    out = []
    for key, rows in results.groupby(list(by)):
        group = " ".join(map(str, key))
        i = rows[check["column"]].idxmax()
        worst = float(rows[check["column"]][i])
        status = "pass" if worst <= check["maximum"] else "fail"
        detail = f"{worst:.1e} ({rows['case'][i]}), maximum {check['maximum']:g}"
        out.append(_result(label, group, status, detail))
    return out


def fitted_order(spacing: Sequence[float], error: Sequence[float]) -> float:
    """``-d log(error) / d log(1/h)``, least squares over all resolutions."""
    return float(-np.polyfit(np.log(1.0 / np.asarray(spacing)), np.log(np.asarray(error)), 1)[0])


def evaluate(
    checks: Sequence[Check], results: pd.DataFrame, folder: Path, by: Sequence[str]
) -> list[Check]:
    """Every check's results; ``folder`` holds the stored tables, ``by`` the group columns."""
    out = []
    for check in checks:
        rows = results
        for column, values in check.get("where", {}).items():
            rows = rows[rows[column].isin(values)]
        if check["type"] == "reference":
            out += reference(check, rows, folder, by)
        elif check["type"] == "order":
            out += order(check, rows, by)
        elif check["type"] == "maximum":
            out += maximum(check, rows, by)
        else:
            raise ValueError(f"unknown check type {check['type']!r}: reference, order or maximum")
    return out
