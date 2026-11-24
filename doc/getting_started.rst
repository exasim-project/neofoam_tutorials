Getting started
===============

Prerequisites
-------------

- `pixi <https://pixi.sh>`_.
- OpenFOAM-v2406, which NeoFOAM's ``pybFoam`` is built against. The environment
  sources it from ``$NEOFOAM_BASHRC`` (default
  ``~/OpenFOAM/OpenFOAM-v2406/etc/bashrc``).
- A NeoFOAM checkout (``$NEOFOAM_SRC``), plus the system compilers OpenFOAM was built
  with. For the ``GPU`` executor, CUDA must be under ``/usr/local/cuda``.

The variables are set in ``pixi.toml`` (``[activation.env]``).

Install
-------

.. code-block:: bash

   pixi install                  # the Python environment (Snakemake, pandas, Sphinx, ...)
   pixi run install-neofoam      # build NeoFOAM from $NEOFOAM_SRC into it
   pixi run install              # register the benchmark solvers (pip install -e .)

``install-neofoam`` builds the C++ core (Kokkos with OpenMP, and CUDA when ``nvcc`` is
found), Ginkgo and ``pybFoam`` into the environment. It takes another checkout as an
argument: ``pixi run install-neofoam ~/src/NeoFOAM``. A first build takes about
40 minutes with 4 jobs and needs about 1.6 GB in ``.pixi/build/neofoam``.

Run benchmarks
--------------

.. code-block:: bash

   pixi run benchmark benchmarks/reconstruction/circle --smoke   # one benchmark, smoke subset
   pixi run benchmark benchmarks/reconstruction/circle           # its full sweep
   pixi run benchmark benchmarks --smoke                         # every benchmark

``FOLDER`` may hold several benchmarks; every ``benchmark.yaml`` below it is run.
Options:

``--smoke``
   Run the benchmark's ``smoke`` subset, which finishes in seconds.
``--method NAME``
   Run method ``NAME`` instead of the variants of the method dimension. Repeatable.
``-c N``
   The number of Snakemake cores (default 4).

The command prints the one Snakemake command it runs, for example:

.. code-block:: text

   snakemake -s results/reconstruction/circle/Snakefile -d results/reconstruction/circle -c 4 report.md

Inside the pixi environment, with OpenFOAM-v2406 sourced, this command alone
reproduces the run. Snakemake reruns only what changed. It does not track the solver's
source code, so after changing a method, add ``--forcerun solve``. The command targets
``report.md``: once the cases are removed, a changed ``plots.py``, reference table or
snapshot reruns ``compare``, ``plots`` and ``report`` only (``--forcerun plots`` redraws
the plots), as they read the collected tables, never the case folders. Snakemake's default
target ``all`` also wants every case and would rerun the solvers.

The command exits non-zero if a workflow failed. The results are not judged: a
**drastic change** against the documentation's snapshot is flagged in ``changes.json``
and in the report, and never fails the workflow (see `Changes against the snapshot`_).

Outputs
-------

Each benchmark writes to ``results/<category>/<name>/`` (gitignored):

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - File
     - Content
   * - ``results.csv``
     - one row per case: its variant of each dimension (``mesh``, ``executor``,
       ``method``, ...) and the last row of its collected tables merged on the time
       (the errors at the end time, maxima over time)
   * - ``histories.csv``
     - with ``collect: {history: true}``: every row of every case's tables (the time
       series the plots draw), with the case's variant columns
   * - ``profiles.csv``
     - with ``collect: {profiles: [...]}``: the cases' profile tables (cavity, pitzDaily),
       with the case's variant columns
   * - ``changes.json``
     - the drastic changes of ``results.csv`` against the documentation's snapshot
       (below): flagged metrics and cases, and the new cases
   * - ``plots/``
     - the benchmark's plots, PNG and PDF
   * - ``report.md``
     - plots, results table and changes on one page
   * - ``Snakefile``, ``sweep.csv``, ``params.yaml``, ``configs/``
     - the exported sweep, kept so the run can be repeated
   * - ``cases/``, ``meshes/``
     - case and mesh data; removed once the workflow succeeds, kept on failure


How a benchmark works
---------------------

A benchmark is a folder ``benchmarks/<category>/<name>/``:

``benchmark.yaml``
   The solver, the sweep and what to do with its results (keys below).
``case/``
   The base case in OpenFOAM format, with ``system/preprocess.yaml`` listing the
   preprocess tools (``blockMesh``, ``setAlphaField``, ...) and
   ``system/postProcess.yaml`` the in-situ tables the solver writes (below).
``reference/``
   Stored tables (CSV) of other codes and the literature, drawn by the plots.
``plots.py``
   ``plot(results, references, out)``, using helpers from
   ``neofoam_tutorials.suite.plots``.
``metrics.py`` (optional)
   What the in-situ tables cannot do: ``derive(history, case) -> DataFrame``, columns
   derived from a case's tables when they are collected (a maximum over time, a ratio),
   and/or ``metrics(case) -> DataFrame``, a table per case from its log or fields.

``pixi run benchmark`` exports ``benchmark.yaml`` as a NeoFOAM ``Sweep`` and runs it:

.. mermaid::

   flowchart LR
     Y["benchmark.yaml<br/>case/"] -->|"export<br/>(NeoFOAM Sweep)"| MESH
     MESH["blockMesh<br/>per mesh variant"] --> SETUP["setup per case<br/>clone, merge payloads,<br/>preprocess tools"]
     SETUP --> SOLVE["solve<br/>neofoam solver NAME"]
     SOLVE --> METRICS["metrics<br/>(optional)"]
     METRICS --> COLLECT["collect<br/>results.csv"]
     SOLVE --> COLLECT
     COLLECT --> COMPARE["compare<br/>changes.json"]
     COLLECT --> PLOTS["plots<br/>plots/"]
     COMPARE --> REPORT["report<br/>report.md"]
     PLOTS --> REPORT

``setup`` lays the case's payloads over the base case, copies the mesh, and runs the
case-level preprocess tools: NeoFOAM's ``setFields`` and ``setAlphaField`` (exact
``cutCellIso`` volume fractions of the level set of the case's
``system/setAlphaField.py``) or this repository's ``setAlphaPlane``. The solvers are
NeoFOAM solvers registered through the ``neofoam.solvers`` (their ``run``) and
``neofoam.region_solvers`` (their spec, for the sweep) entry points in
``pyproject.toml``:

- ``reconstructInterface``: TwoPhaseFlow's ``reconstructInterface``.
- ``advectorVoF``: TwoPhaseFlow's ``advectorVoF``, with NeoN isoAdvector or MULES.
- ``incompressibleVoFNeoNSweep``: NeoFOAM's ``incompressibleVoFNeoN``.
- ``incompressibleFluidNeoNSweep``: NeoFOAM's ``incompressibleFluidNeoN`` (single phase).

They are built from NeoFOAM's models only, and write tables with the same columns as
the reference applications. Snakemake tracks ``benchmark.yaml``'s ``collect`` section, ``plots.py``,
``metrics.py``, the reference tables and the snapshot, so changing a plot reruns only
``plots`` and ``report``.

In-situ tables
~~~~~~~~~~~~~~

The solvers run NeoFOAM's ``postProcess`` model: ``case/system/postProcess.yaml``
declares tables, each a source, a pipeline of nodes and a write control, and the solver
appends a row per evaluation to ``postProcessing/<name>.csv`` (NeoFOAM's
``doc/reference/postprocessing.rst``). For example the static drop's spurious current
and the pressure inside the drop, at the field write times:

.. code-block:: yaml

   tables:
     - name: maxU
       source: {type: internal, field: U}
       pipeline: [{type: mag}, {type: max, name: maxU}]
       write_control: {write_control_type: stepper}
     - name: p_inside
       source: {type: internal, field: p_rgh}
       pipeline:
         - {type: sphere, center: [0.004, 0.004, 0.0001], radius: 0.001}
         - {type: mean, name: p_inside}
       write_control: {write_control_type: stepper}

On the NeoN solvers only the ``internal`` source works, on the registry fields
(``alpha1``, ``U``, ``p_rgh``, ``p``, ``rho``). This repository adds the sources
``shapeError`` (TwoPhaseFlow's Eshape integrand) and ``startField`` (a field at the start
time) and the nodes ``hydrostaticError`` and ``change``, registered through the
``neofoam.plugins`` entry point ``neofoam_tutorials.postprocess``.

``benchmark.yaml`` keys
~~~~~~~~~~~~~~~~~~~~~~~

``solver``
   The ``neofoam solver`` name.
``merge``
   ``true``: each payload is laid over the base case's config.
``dimensions``
   Dimension (a config of the solver, e.g. ``block_mesh_dict_config``,
   ``neo_n_control_config``) → variant → payload. This is NeoFOAM's ``params.yaml``
   shape. Cases are the cross product. The ``mesh`` dimension holds the resolutions.
``smoke``
   Dimension → the variants that ``--smoke`` keeps.
``method``
   ``{dimension, entry}``: the dimension that ``--method NAME`` replaces by
   ``{NAME: {entry: NAME}}``.
``metrics``
   ``{script, prune}``: the per-case metrics script, and whether to prune time
   directories.
``collect``
   ``tables``: the case's tables, NeoFOAM ``postProcess`` CSVs and function-object
   ``.dat`` files, merged on the time (a later table's column replaces an earlier one);
   ``derive``: ``metrics.py`` with ``derive(history, case)``, columns added to the
   merged table; ``history``: ``true`` writes ``histories.csv``; ``profiles``: per-case
   files concatenated into ``profiles.csv``; ``columns``: dimension → column name in
   ``results.csv``, whose row per case is the last row of the merged table.
``report``
   The columns of the report's results table.

Changes against the snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The suite shows NeoFOAM's results; it does not hold them to a tolerance. ``compare``
(``neofoam_tutorials.suite.changes``) only flags what moved a lot since the snapshot in
``doc/_generated/<category>/<name>/results.csv``, its rows matched to the run's by the
dimension columns (``mesh``, ``executor``, ``method``, ...):

- **ratio**: a numeric column whose run value is more than 2× or less than 0.5× the
  snapshot's (a sign change too);
- **nan**: a column that has a value in the snapshot and is NaN (or absent) in the run;
- **missing**: a case of the snapshot that the run does not have.

A case only in the run (a new mesh or ``--method``) is listed as **new**, not flagged.
Every numeric column is compared but the timings (TwoPhaseFlow's ``tRec``, ``Tadv``,
``k1``, ``k2`` and any column ending in ``_s``, e.g. ``wall_s``), and a pair of values
both below 1e-10 in magnitude (round-off) is not compared; there is no per-column
setting.

Add a benchmark
---------------

1. Create ``benchmarks/<category>/<name>/`` with ``case/`` (including
   ``system/preprocess.yaml``), ``benchmark.yaml``, ``plots.py`` and the stored tables
   in ``reference/``. Copying the closest existing benchmark is the quickest start.
2. Give the case literal values. The dimensions' payloads override them per case.
3. Declare the metrics as in-situ tables in ``case/system/postProcess.yaml`` and list
   their CSVs in ``collect.tables``; derive what a table cannot hold (a maximum over
   time, a ratio of two tables) in ``metrics.py``'s ``derive`` (``collect.derive``). For
   what needs the log or a whole field, add ``metrics(case)`` and ``metrics: {script:
   metrics.py, prune: true}``, and collect ``postProcessing/metrics.dat``. Plots read
   ``histories.csv`` and ``profiles.csv`` (``histories()``, ``profiles()``), never the
   cases.
4. Run ``pixi run benchmark benchmarks/<category>/<name> --smoke`` and check
   ``report.md``.

A new solver is a module that exports the solver spec and ``run(argv)``, registered
under ``[project.entry-points."neofoam.solvers"]`` (``module:run``) and
``[project.entry-points."neofoam.region_solvers"]`` (``module:spec``) in
``pyproject.toml`` (then ``pixi run install``). A new preprocess tool is registered under
``neofoam.plugins``, like ``setAlphaPlane``.

Test a new method
-----------------

A reconstruction or advection scheme registered with NeoFOAM (for example through a
``neofoam.plugins`` entry point) needs no change to the benchmark:

.. code-block:: bash

   pixi run benchmark benchmarks/reconstruction/circle --method myScheme --smoke

This runs the cases ``n8_Serial_myScheme`` and ``n16_Serial_myScheme`` and reports
their errors; against the snapshot they are new cases, listed but not flagged.
To keep the method in the default sweep, add it as a variant of the method dimension
in ``benchmark.yaml``.

Change sweeps
-------------

Edit ``benchmark.yaml``. To add a resolution, add a variant to ``mesh`` (most
``benchmark.yaml`` files note their larger meshes in a comment). Then rerun the printed Snakemake command: only
the affected steps run again.

.. _refresh-the-results:

Refresh the results in this documentation
-----------------------------------------

The pages show a committed snapshot in ``doc/_generated/``, so the documentation builds
without rerunning benchmarks. To update it, run the benchmarks and then build:

.. code-block:: bash

   pixi run benchmark benchmarks          # or a single benchmark
   pixi run docs                          # sync results/ into doc/_generated/, build

``pixi run docs`` runs ``doc/_scripts/sync_results.py``. The script copies
``results.csv``, ``changes.json`` and the shrunk ``plots/*.png`` of every benchmark
that has a run in ``results/``, renders the tables, and builds the HTML with
``sphinx-build -W`` into ``doc/_build/html``. Commit ``doc/_generated/`` to keep the
new snapshot. A page notes when its snapshot holds only part of the full sweep.

The readable tables of each page (changed parameters, key results, changes since the
previous snapshot) are rendered from ``benchmark.yaml``, ``results.csv`` and
``changes.json`` at build time by ``doc/_scripts/page_tables.py`` and
``doc/_scripts/sync_results.py``. The setup sketches in ``doc/_static/setup/`` are drawn
from the case files; after changing a case, redraw and commit them:

.. code-block:: bash

   pixi run python doc/_scripts/setup_sketches.py                  # all
   pixi run python doc/_scripts/setup_sketches.py reconstruction/circle
