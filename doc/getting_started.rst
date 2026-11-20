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
``report.md``: once the cases are removed, a changed ``plots.py``, check or reference
table reruns ``verify``, ``plots`` and ``report`` only (``--forcerun plots`` redraws the
plots), as they read the collected tables, never the case folders. Snakemake's default
target ``all`` also wants every case and would rerun the solvers.

The command exits non-zero if a workflow failed. A failed **check** does not fail the
workflow; it is recorded in ``checks.json`` and in the report.

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
   * - ``checks.json``
     - every check's result per group of cases (``pass``, ``fail``, ``skip``) with a
       detail line
   * - ``plots/``
     - the benchmark's plots, PNG and PDF
   * - ``report.md``
     - plots, results table and checks on one page
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
   Stored tables (CSV), read by the checks and the plots.
``plots.py``
   ``plot(results, references, out)``, using helpers from
   ``neofoam_verification.suite.plots``.
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
     COLLECT --> VERIFY["verify<br/>checks.json"]
     COLLECT --> PLOTS["plots<br/>plots/"]
     VERIFY --> REPORT["report<br/>report.md"]
     PLOTS --> REPORT

``setup`` lays the case's payloads over the base case, copies the mesh, and runs the
case-level preprocess tools: NeoFOAM's ``setAlphaField`` (exact ``cutCellIso`` volume
fractions of a cylinder or sphere) or this repository's ``setAlphaPlane``. The solvers
are NeoFOAM solvers registered through the ``neofoam.solvers`` entry point in
``pyproject.toml``:

- ``reconstructInterface``: TwoPhaseFlow's ``reconstructInterface``.
- ``advectorVoF``: TwoPhaseFlow's ``advectorVoF``, with NeoN isoAdvector or MULES.
- ``incompressibleVoFNeoNSweep``: NeoFOAM's ``incompressibleVoFNeoN``.
- ``incompressibleFluidNeoNSweep``: NeoFOAM's ``incompressibleFluidNeoN`` (single phase).

They are built from NeoFOAM's models only, and write tables with the same columns as
the reference applications. Snakemake tracks ``benchmark.yaml``, ``plots.py``,
``metrics.py`` and the reference tables, so changing a check reruns only ``verify`` and
``report``.

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
``neofoam.plugins`` entry point ``neofoam_verification.postprocess``.

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
``checks``
   A list of checks (below).
``report``
   The columns of the report's results table.

Checks
~~~~~~

Checks run per group of cases. A group is one combination of every dimension except
the mesh (for example ``MULES CFL01 Serial``), so a check sees all resolutions of a
group.

``{type: reference, file, match, columns, rtol}``
   Compare ``columns`` with ``reference/<file>``, rows matched on the ``match`` columns,
   to relative tolerance ``rtol``. Empty stored values are not compared, and a group
   without stored rows is skipped.
``{type: order, column, spacing, minimum}``
   The least-squares slope of ``log(column)`` over ``log(1/spacing)`` must be at least
   ``minimum``.
``{type: maximum, column, maximum}``
   The group's largest value must be at most ``maximum``: a mass or bound error, or a
   spurious velocity.
``{type: agreement, across, base, columns, rtol}``
   Each case must agree with the same case of the ``base`` variant of ``across`` to
   ``rtol``, for example ``CPU`` and ``GPU`` against ``Serial``.

``where: {column: [values]}`` limits any check to those rows.

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
under ``[project.entry-points."neofoam.solvers"]`` in ``pyproject.toml`` (then
``pixi run install``). A new preprocess tool is registered under ``neofoam.plugins``,
like ``setAlphaPlane``.

Test a new method
-----------------

A reconstruction or advection scheme registered with NeoFOAM (for example through a
``neofoam.plugins`` entry point) needs no change to the benchmark:

.. code-block:: bash

   pixi run benchmark benchmarks/reconstruction/circle --method myScheme --smoke

This runs the cases ``n8_Serial_myScheme`` and ``n16_Serial_myScheme`` and reports
their errors and checks. A ``reference`` check skips groups that have no stored rows.
To keep the method in the default sweep, add it as a variant of the method dimension
in ``benchmark.yaml``.

Change sweeps and thresholds
----------------------------

Edit ``benchmark.yaml``. To add a resolution, add a variant to ``mesh`` (each
benchmark page lists its larger meshes). To tighten or relax a check, change its
``rtol``, ``minimum`` or ``maximum``; record the measured value and the reason in a
comment next to it, as the existing checks do. Then rerun the printed Snakemake
command: only the affected steps run again.

.. _refresh-the-results:

Refresh the results in this documentation
-----------------------------------------

The pages show a committed snapshot in ``doc/_generated/``, so the documentation builds
without rerunning benchmarks. To update it, run the benchmarks and then build:

.. code-block:: bash

   pixi run benchmark benchmarks          # or a single benchmark
   pixi run docs                          # sync results/ into doc/_generated/, build

``pixi run docs`` runs ``doc/_scripts/sync_results.py``. The script copies
``results.csv``, ``checks.json`` and the shrunk ``plots/*.png`` of every benchmark
that has a run in ``results/``, renders the tables, and builds the HTML with
``sphinx-build -W`` into ``doc/_build/html``. Commit ``doc/_generated/`` to keep the
new snapshot. A page notes when its snapshot holds only part of the full sweep.

The readable tables of each page (changed parameters, key results, check verdicts) are
rendered from ``benchmark.yaml``, ``results.csv`` and ``checks.json`` at build time by
``doc/_scripts/page_tables.py``. The setup sketches in ``doc/_static/setup/`` are drawn
from the case files; after changing a case, redraw and commit them:

.. code-block:: bash

   pixi run python doc/_scripts/setup_sketches.py                  # all
   pixi run python doc/_scripts/setup_sketches.py reconstruction/circle
