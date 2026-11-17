"""The circle reconstruction verification case's building blocks and its published reference.

The interface centres and the error definition are TwoPhaseFlow's (``reconstructInterface``,
``reconstructionError``); numufoam's ``error.csv``
(``benchmarks/reconstruction/circle/reference/``) is the published run of the same case.
The ``openfoam`` test runs the coarsest resolutions of ``benchmarks/reconstruction/circle/case``
with TwoPhaseFlow's reconstructInterface (OpenFOAM-v2506).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from foamlib import FoamFile

from neofoam_verification.foam_random import centres
from neofoam_verification.reconstruction_error import (
    ReconstructionError,
    observed_order,
    read_error_dat,
    read_numufoam,
    sample_errors,
)
from neofoam_verification.shapes import Cylinder

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "reconstruction" / "circle"
CASE = BENCHMARK / "case"
NUMUFOAM = read_numufoam(BENCHMARK / "reference" / "numufoam_error.csv")
SCHEMES = ("isoAlpha", "plicRDF", "gradAlpha")
NORMS = ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1")

# reconstructInterface's log ("centre (x y z)", writePrecision 17) of the circle case
LOGGED_CENTRES = np.array(
    [
        [1.0878855217857544, 0, 0.97443629964981937],
        [1.0972591172088473, 0, 0.93582405910630817],
        [1.0257658133431258, 0, 0.91099023637235876],
        [0.92557657194070997, 0, 0.94332249869011919],
        [0.92464754400267557, 0, 1.0847629646164472],
        [0.92385741347478489, 0, 1.051489085363505],
        [1.0469269583891947, 0, 1.0925552821071121],
        [1.0750231410959894, 0, 1.0178913502986584],
        [0.92728898690711803, 0, 1.072973156041406],
        [0.9180053060437019, 0, 0.96839075325581381],
    ]
)


def test_centres_are_reconstructInterface_sequence() -> None:
    np.testing.assert_array_equal(centres(np.array([1.01, 0.0, 1.01]), 10), LOGGED_CENTRES)


def test_sample_errors_of_tilted_and_shifted_planes() -> None:
    circle = Cylinder(origin=(1.0, 0.0, 1.0), radius=0.5, direction=(0.0, 1.0, 0.0))
    theta = np.linspace(0.0, 2.0 * np.pi, 7, endpoint=False)
    radial = np.column_stack([np.cos(theta), np.zeros_like(theta), np.sin(theta)])
    tilt, shift = 1e-3, 2e-4
    rotated = np.cos(tilt) * -radial + np.sin(tilt) * np.cross(radial, [0.0, 1.0, 0.0])
    centre = np.array(circle.origin) + (0.5 + shift) * radial
    # a zero normal marks a cell without interface; its centre is never looked at
    normal_error, centre_error = sample_errors(
        circle, np.vstack([centre, [0.0, 0.0, 0.0]]), np.vstack([3.0 * rotated, [0, 0, 0]])
    )

    np.testing.assert_allclose(normal_error, 1.0 - np.cos(tilt), rtol=1e-8)
    np.testing.assert_allclose(centre_error, shift, rtol=1e-10)


def test_error_norms_aggregate_like_calcError() -> None:
    errors = ReconstructionError()
    errors.add(np.array([1.0, 3.0]), np.array([0.5, 0.5]))
    errors.add(np.array([2.0]), np.array([4.0, 0.0]))

    assert errors.norms == {"LNormalInf": 3.0, "LNormal1": 2.0, "LCentreInf": 4.0, "LCentre1": 1.25}


@pytest.mark.parametrize("norm", NORMS)
def test_numufoam_plicRDF_converges_second_order(norm: str) -> None:
    resolutions = sorted(n for scheme, n in NUMUFOAM if scheme == "plicRDF")
    spacing = np.array([NUMUFOAM["plicRDF", n]["length"] for n in resolutions])
    error = np.array([NUMUFOAM["plicRDF", n][norm] for n in resolutions])

    fitted = -np.polyfit(np.log(1.0 / spacing), np.log(error), 1)[0]
    assert 1.8 < fitted < 2.3, observed_order(spacing, error)


def _have_reconstruct_interface() -> bool:
    bashrc = Path(os.environ.get("TWOPHASEFLOW_BASHRC", ""))
    check = f'source "{bashrc}" >/dev/null 2>&1 && command -v reconstructInterface'
    return bashrc.is_file() and subprocess.run(["bash", "-c", check]).returncode == 0


@pytest.mark.openfoam
@pytest.mark.skipif(
    not _have_reconstruct_interface(), reason="no TwoPhaseFlow reconstructInterface"
)
@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("n", [8, 16])
def test_reconstructInterface_reproduces_numufoam(tmp_path: Path, scheme: str, n: int) -> None:
    case = tmp_path / "case"
    shutil.copytree(CASE, case)
    parameters = FoamFile(case / "system" / "simulationParameters")
    parameters["nx"] = n
    parameters["nz"] = n
    parameters["reconScheme"] = scheme
    command = (
        f'source "{os.environ["TWOPHASEFLOW_BASHRC"]}" >/dev/null 2>&1 && blockMesh > log.blockMesh'
        " && cp -r 0.orig 0 && reconstructInterface > log.reconstructInterface 2>&1"
    )
    subprocess.run(["bash", "-c", command], cwd=case, check=True)

    result = read_error_dat(case / "postProcessing" / "reconstructionError" / "0" / "error.dat")
    for norm in (*NORMS, "length", "nCells"):
        # numufoam's run agrees to ~1e-11 relative (a different build of the same code)
        np.testing.assert_allclose(result[norm], NUMUFOAM[scheme, n][norm], rtol=1e-9, err_msg=norm)
