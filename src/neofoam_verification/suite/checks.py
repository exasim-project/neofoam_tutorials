"""The declarative checks of ``benchmark.yaml`` on ``results.csv``.

Each check is evaluated per group of cases (the columns of the dimensions but the mesh:
executor and method) and gives one result ``{check, group, status, detail}``, status
``pass``, ``fail`` or ``skip`` (nothing to compare):

* ``{type: reference, file, match, columns, rtol}`` -- the stored table ``reference/<file>``,
  its rows matched to the results' by the ``match`` columns, every ``columns`` value to
  ``rtol`` relative (an empty stored value is not compared);
* ``{type: order, column, spacing, minimum}`` -- the observed order, the least-squares
  slope of ``log(column)`` over ``log(spacing)`` across the group's resolutions, at least
  ``minimum``;
* ``{type: maximum, column, maximum}`` -- the group's largest ``column`` value at most
  ``maximum`` (an absolute bound: a spurious velocity, a relative pressure error);
* ``{type: agreement, columns, across, base, rtol}`` -- the ``columns`` of each case
  within ``rtol`` relative of the same case (every other dimension equal) with the
  ``base`` variant of ``across`` (default its first in the results; e.g. the CPU and GPU
  executors against Serial); one result per other ``across`` variant.
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


def _max_rel_diff(pairs: pd.DataFrame, expected: dict[str, str]) -> tuple[float, str]:
    """The largest relative difference of each column to its ``expected`` column, and where."""
    worst, where = 0.0, ""
    for column, reference_column in expected.items():
        ref = pairs[reference_column].to_numpy(float)
        diff = np.abs(pairs[column].to_numpy(float) - ref)
        diff /= np.maximum(np.abs(ref), np.finfo(float).tiny)
        # a stored row without this column's value (empty) is not compared
        if np.isnan(diff).all():
            continue
        i = int(np.nanargmax(diff))
        if diff[i] >= worst:
            worst, where = float(diff[i]), f"{column} {pairs['case'].iloc[i]}"
    return worst, where


def reference(check: Check, results: pd.DataFrame, folder: Path, by: Sequence[str]) -> list[Check]:
    on, columns = list(check["match"]), list(check["columns"])
    stored = pd.read_csv(folder / check["file"])
    stored = stored.astype({c: results[c].dtype for c in on})
    label = f"reference {check['file']} {','.join(columns)}"
    out = []
    for key, rows in results.groupby(list(by)):
        group = " ".join(map(str, key))
        pairs = rows.merge(stored, on=on, suffixes=("", "_ref"))
        if pairs.empty:
            out.append(_result(label, group, "skip", "no stored row for these cases"))
            continue
        worst, where = _max_rel_diff(pairs, {c: c if c in on else f"{c}_ref" for c in columns})
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
        detail = f"{worst:.3e} ({rows['case'][i]}), maximum {check['maximum']:g}"
        out.append(_result(label, group, status, detail))
    return out


def agreement(check: Check, results: pd.DataFrame, by: Sequence[str], mesh: str) -> list[Check]:
    across, columns = check["across"], list(check["columns"])
    label = f"agreement {across}"
    variants = list(dict.fromkeys(results[across]))
    base = check.get("base", variants[0])
    others = [v for v in variants if v != base]
    if not others:
        return [_result(label, base, "skip", f"one {across} variant")]
    key = [*(c for c in by if c != across), mesh]
    reference = results[results[across] == base]
    out = []
    for other in others:
        pairs = results[results[across] == other].merge(reference, on=key, suffixes=("", "_ref"))
        worst, where = _max_rel_diff(pairs, {c: f"{c}_ref" for c in columns})
        status = "pass" if worst <= check["rtol"] else "fail"
        detail = f"max rel diff {worst:.1e} ({where}), rtol {check['rtol']:g}, {len(pairs)} cases"
        out.append(_result(label, f"{other} vs {base}", status, detail))
    return out


def fitted_order(spacing: Sequence[float], error: Sequence[float]) -> float:
    """``-d log(error) / d log(1/h)``, least squares over all resolutions."""
    return float(-np.polyfit(np.log(1.0 / np.asarray(spacing)), np.log(np.asarray(error)), 1)[0])


def evaluate(
    checks: Sequence[Check],
    results: pd.DataFrame,
    folder: Path,
    by: Sequence[str],
    mesh: str = "mesh",
) -> list[Check]:
    """Every check's results; ``folder`` holds the stored tables, ``by`` the group columns,
    ``mesh`` the mesh column (``agreement`` pairs the cases on it and ``by``)."""
    out = []
    for check in checks:
        if check["type"] == "reference":
            out += reference(check, results, folder, by)
        elif check["type"] == "order":
            out += order(check, results, by)
        elif check["type"] == "maximum":
            out += maximum(check, results, by)
        elif check["type"] == "agreement":
            out += agreement(check, results, by, mesh)
        else:
            raise ValueError(
                f"unknown check type {check['type']!r}: reference, order, maximum or agreement"
            )
    return out
