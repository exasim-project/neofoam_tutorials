"""Circle reconstruction on hex meshes (arXiv 1801.05382 sec. 4.1.1, numufoam's circle).

The errors are TwoPhaseFlow's ``reconstructionError`` against the exact circle; the
reference backend is TwoPhaseFlow's ``reconstructInterface`` (v2506), published numbers
are numufoam's ``error.csv``.
"""

from pathlib import Path

from neofoam_verification.reconstruction_error import COLUMNS, read_numufoam
from neofoam_verification.solvers.reconstruction_io import ERROR_DAT, alpha_samples
from neofoam_verification.suite.backends import NEOFOAM_BACKENDS
from neofoam_verification.suite.benchmark import Benchmark, FunctionObjectTable, Step, Sweep
from neofoam_verification.suite.checks import AgainstBackend, Order, Published
from neofoam_verification.suite.plots import ErrorPlot, TimingPlot

HERE = Path(__file__).resolve().parent
NORMS = ("LNormalInf", "LNormal1", "LCentreInf", "LCentre1")

BENCHMARK = Benchmark(
    case=HERE / "case",
    solver="reconstructInterface",
    sweep=Sweep(
        resolutions=(8, 16, 32, 64, 128, 256, 512, 1024),
        smoke=(8, 16),
        methods=("gradAlpha",),
        parameters=lambda n, method: {"nx": n, "nz": n, "reconScheme": method},
    ),
    prepare=(
        Step("blockMesh"),
        Step("setAlphaField", "setAlphaField -dict system/initAlphaFieldDict"),
        # reconstructInterface sets its samples itself; NeoFOAM's solver reads them
        Step("alphaSamples", alpha_samples, backends=NEOFOAM_BACKENDS),
    ),
    backends=("twophaseflow", *NEOFOAM_BACKENDS),
    table=FunctionObjectTable(ERROR_DAT.as_posix(), COLUMNS, timing=("k1", "k2")),
    report_columns=NORMS,
    results_columns=("nCells", "length", *NORMS, "k1", "wall_s"),
    plots=(
        ErrorPlot(NORMS),
        # TwoPhaseFlow's k1 is CPU time with 1 ms resolution (0 below x64), NeoFOAM's wall time
        TimingPlot("k1", "reconstruction time per sample, k1", name="k1"),
        TimingPlot("wall_s", "solver wall time", name="wall"),
    ),
    reference_backend="twophaseflow",
    checks=(
        # numufoam's run of the same case reproduces to ~1e-11 relative (TwoPhaseFlow only:
        # NeoFOAM is held to the TwoPhaseFlow table)
        Published(
            "numufoam_error.csv",
            read_numufoam,
            (*NORMS, "length", "nCells"),
            rtol=1e-9,
            backends=("twophaseflow",),
        ),
        AgainstBackend("twophaseflow", (*NORMS, "length", "nCells"), rtol=1e-6),
        # the centre is second order for any scheme; the normal is not for gradAlpha
        Order("LCentre1", minimum=1.5),
        Order("LCentreInf", minimum=1.5),
    ),
)
