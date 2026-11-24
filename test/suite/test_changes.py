"""The drastic-change flag of a run's results against the snapshot, on small tables.

Each case is a snapshot row and a run row of the same shape as ``results.csv`` (``case``,
the dimension columns ``mesh`` and ``executor``, metrics), and the expected findings.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from neofoam_tutorials.suite.changes import compare

KEYS = ["executor", "mesh"]
NAN = math.nan


def _table(rows: list[tuple[str, str, float, float]]) -> pd.DataFrame:
    """Rows ``(executor, mesh, Eshape, wall_s)`` as a results table."""
    return pd.DataFrame(
        [
            {"case": f"{m}_{e}", "executor": e, "mesh": m, "Eshape": eshape, "wall_s": wall}
            for e, m, eshape, wall in rows
        ]
    )


@pytest.mark.parametrize(
    "old, new, expected",
    [
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0)], [("Serial", "n10", 1.9e-2, 1.6)], [], id="within-2x"
        ),
        pytest.param([("Serial", "n10", 0.0, 3.0)], [("Serial", "n10", 0.0, 3.0)], [], id="zero"),
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0)],
            [("Serial", "n10", 2.1e-2, 1.4)],
            [
                {
                    "case": "n10_Serial",
                    "column": "Eshape",
                    "kind": "ratio",
                    "old": 1e-2,
                    "new": 2.1e-2,
                },
                {"case": "n10_Serial", "column": "wall_s", "kind": "ratio", "old": 3.0, "new": 1.4},
            ],
            id="beyond-2x-up-and-down",
        ),
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0)],
            [("Serial", "n10", -1e-2, 3.0)],
            [
                {
                    "case": "n10_Serial",
                    "column": "Eshape",
                    "kind": "ratio",
                    "old": 1e-2,
                    "new": -1e-2,
                }
            ],
            id="sign-change",
        ),
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0)],
            [("Serial", "n10", NAN, 3.0)],
            [{"case": "n10_Serial", "column": "Eshape", "kind": "nan", "old": 1e-2, "new": None}],
            id="nan-in-run",
        ),
        pytest.param(
            [("Serial", "n10", NAN, 3.0)], [("Serial", "n10", 1e-2, 3.0)], [], id="nan-in-snapshot"
        ),
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0), ("GPU", "n10", 1e-2, 1.0)],
            [("Serial", "n10", 1e-2, 3.0)],
            [{"case": "n10_GPU", "column": "", "kind": "missing", "old": None, "new": None}],
            id="missing-case",
        ),
        pytest.param(
            [("Serial", "n10", 1e-2, 3.0)],
            [("Serial", "n10", 1e-2, 3.0), ("Serial", "n20", 5e-3, 6.0)],
            [{"case": "n20_Serial", "column": "", "kind": "new", "old": None, "new": None}],
            id="new-case",
        ),
    ],
)
def test_compare_flags_drastic_changes_per_case_and_metric(
    old: list[tuple[str, str, float, float]],
    new: list[tuple[str, str, float, float]],
    expected: list[dict[str, object]],
) -> None:
    changes = compare(_table(new), _table(old), KEYS)

    assert changes == expected


def test_compare_counts_a_metric_missing_in_the_run_as_nan() -> None:
    old = _table([("Serial", "n10", 1e-2, 3.0)])
    new = old.drop(columns="wall_s")

    changes = compare(new, old, KEYS)

    assert changes == [
        {"case": "n10_Serial", "column": "wall_s", "kind": "nan", "old": 3.0, "new": None}
    ]
