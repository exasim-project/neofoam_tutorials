NeoFOAM verification
====================

``neofoam_tutorials`` showcases the verification state of NeoFOAM's single-phase
incompressible solver and its two-phase volume-of-fluid (VoF) methods on TwoPhaseFlow's
and other published benchmarks. Each benchmark is a base case and a parameter sweep;
its results are shown next to stored reference data from OpenFOAM, TwoPhaseFlow,
numufoam or the literature. The suite does not judge the results: it only flags a
result that changed drastically since the previous snapshot.
The suite runs each benchmark as a NeoFOAM sweep with Snakemake, on NeoN's ``Serial``,
``CPU`` and ``GPU`` executors. These pages show the results: what NeoFOAM reproduces,
and where it does not yet match the methods it is compared against.

.. toctree::
   :maxdepth: 2

   getting_started
   single_phase/index
   multiphase/index
