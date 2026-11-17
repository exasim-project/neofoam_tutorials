NeoFOAM verification
====================

``neofoam_verification`` is the verification suite for NeoFOAM's two-phase
volume-of-fluid (VoF) methods. Each benchmark is a base case, a parameter sweep and
declarative checks against stored references from OpenFOAM, TwoPhaseFlow or numufoam.
The suite runs each benchmark as a NeoFOAM sweep with Snakemake, on NeoN's ``Serial``,
``CPU`` and ``GPU`` executors. These pages show the results: what NeoFOAM reproduces,
and where it does not yet match the methods it is compared against.

.. toctree::
   :maxdepth: 2

   getting_started
   multiphase/index
