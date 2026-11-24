Multiphase
==========

These benchmarks cover the building blocks of a geometric VoF solver: interface
reconstruction, interface advection, surface tension, and gravity across the interface.
Each page says what is tested and why, describes the case and the parameter changes,
and shows and explains the results.

- :doc:`circle`: interface reconstruction (PLIC, gradAlpha) of a circle on hex meshes.
- :doc:`disc_uni_flow`: advection of a disc in uniform flow, against numufoam.
- :doc:`disc_uni_flow_testsuite`: advection of a disc for t = 4, against TwoPhaseFlow's ``advectorVoF``.
- :doc:`static_drop`: surface tension: parasitic currents of a static drop (CSF).
- :doc:`tilted_box`: hydrostatic balance in a tilted box (gravity, no surface tension).

.. toctree::
   :maxdepth: 1

   circle
   disc_uni_flow
   disc_uni_flow_testsuite
   static_drop
   tilted_box
