# The benchmark's rules after NeoFOAM's sweep, included by the Snakefile that
# neofoam_verification.suite.benchmark.export writes: (metrics per case ->) collect ->
# verify, plots -> report.
# Consumes the sweep's globals `cases` and BASE_CASE (the benchmark's case/ folder).
from pathlib import Path

import yaml

BENCHMARK = str(Path(BASE_CASE).parent)
BENCHMARK_WORKER = "python -m neofoam_verification.suite.workflow"
REFERENCES = sorted(str(p) for p in Path(BENCHMARK, "reference").glob("*.csv"))
METRICS = yaml.safe_load(Path(BENCHMARK, "benchmark.yaml").read_text()).get("metrics")
# what collect reads of a case: the solved case, or its metrics table
CASE_RESULT = "cases/{case}/postProcessing/metrics.dat" if METRICS else "cases/{case}/done"


if METRICS:

    rule metrics:
        input:
            "cases/{case}/done",
            BENCHMARK + "/" + METRICS["script"],
        output:
            "cases/{case}/postProcessing/metrics.dat"
        shell:
            BENCHMARK_WORKER + " metrics --benchmark '{BENCHMARK}' --out '{output}'"


rule collect:
    input:
        expand(CASE_RESULT, case=cases),
        "sweep.csv",
        BENCHMARK + "/benchmark.yaml",
    output:
        "results.csv"
    shell:
        BENCHMARK_WORKER + " collect --benchmark '{BENCHMARK}' --out '{output}'"


rule verify:
    input:
        "results.csv",
        BENCHMARK + "/benchmark.yaml",
        REFERENCES,
    output:
        "checks.json"
    shell:
        BENCHMARK_WORKER + " verify --benchmark '{BENCHMARK}' --out '{output}'"


rule plots:
    input:
        "results.csv",
        BENCHMARK + "/plots.py",
        REFERENCES,
    output:
        directory("plots")
    shell:
        BENCHMARK_WORKER + " plots --benchmark '{BENCHMARK}' --out '{output}'"


rule report:
    input:
        "results.csv",
        "checks.json",
        "plots",
    output:
        "report.md"
    shell:
        BENCHMARK_WORKER + " report --benchmark '{BENCHMARK}' --out '{output}'"
