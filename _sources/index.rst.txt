NeoFOAM verification
====================

``neofoam_tutorials`` is the verification suite for NeoFOAM's single-phase
incompressible solver and its two-phase volume-of-fluid (VoF) methods. Each benchmark is
a base case, a parameter sweep and declarative checks against stored references from
OpenFOAM, TwoPhaseFlow, numufoam or the literature.
The suite runs each benchmark as a NeoFOAM sweep with Snakemake, on NeoN's ``Serial``,
``CPU`` and ``GPU`` executors. These pages show the results: what NeoFOAM reproduces,
and where it does not yet match the methods it is compared against.

.. toctree::
   :maxdepth: 2

   getting_started
   single_phase/index
   multiphase/index
