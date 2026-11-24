# The benchmark's rules after NeoFOAM's sweep, included by the Snakefile that
# neofoam_tutorials.suite.benchmark.export writes: (metrics per case ->) collect ->
# verify, plots -> report; on success the case and mesh data are removed.
# Consumes the sweep's globals `cases` and BASE_CASE (the benchmark's case/ folder).
# Only collect (and metrics) read the cases: verify, plots and report read collect's
# tables, so a changed check or plots.py reruns them alone, also once cases/ is gone
# (target report.md, as `pixi run benchmark` does; the Snakefile's `all` wants the cases).
import json
from pathlib import Path

import yaml

BENCHMARK = str(Path(BASE_CASE).parent)
BENCHMARK_WORKER = "python -m neofoam_tutorials.suite.workflow"
REFERENCES = sorted(str(p) for p in Path(BENCHMARK, "reference").glob("*.csv"))
SPEC = yaml.safe_load(Path(BENCHMARK, "benchmark.yaml").read_text())
METRICS = SPEC.get("metrics")
COLLECT = SPEC["collect"]
# collect's outputs: results.csv, with collect.history / collect.profiles the tables beside it
TABLES = ["results.csv"]
TABLES += ["histories.csv"] if COLLECT.get("history", False) else []
TABLES += ["profiles.csv"] if COLLECT.get("profiles") else []
DERIVE = [BENCHMARK + "/" + COLLECT["derive"]] if "derive" in COLLECT else []
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


# collect reruns on a change of benchmark.yaml's collect section (params), not of the
# whole file: a changed check must not need the cases
rule collect:
    input:
        expand(CASE_RESULT, case=cases),
        "sweep.csv",
        DERIVE,
    params:
        collect=json.dumps(COLLECT, sort_keys=True),
    output:
        TABLES
    shell:
        BENCHMARK_WORKER + " collect --benchmark '{BENCHMARK}' --out '{output[0]}'"


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
        TABLES,
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


# Keep only the outputs (results.csv, checks.json, plots/, report.md) and the small
# sweep files that rerun the workflow; the case and mesh data go once the run succeeded.
onsuccess:
    shell("rm -rf cases meshes")
