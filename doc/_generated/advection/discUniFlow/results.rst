.. note::

   This snapshot holds 2 of the 36 cases of the full sweep (a ``--smoke`` run). Run the full sweep and refresh the snapshot (:ref:`refresh-the-results`) for all of them.

.. list-table::
   :header-rows: 1
   :widths: auto

   * - ``method``
     - ``CFL``
     - ``executor``
     - ``mesh``
     - ``Ncells``
     - ``Eshape``
     - ``Emass``
     - ``Ebound``
     - ``Tadv``
     - ``wall_s``
     - ``steps``
   * - MULES
     - CFL01
     - Serial
     - n10
     - 100
     - 0.01607
     - 1.388e-17
     - 2.883e-19
     - 0.0001127
     - 0.2311
     - 100
   * - isoAdvector
     - CFL01
     - Serial
     - n10
     - 100
     - 0.006916
     - 2.776e-17
     - 5.242e-17
     - 0.0001046
     - 0.2744
     - 100
