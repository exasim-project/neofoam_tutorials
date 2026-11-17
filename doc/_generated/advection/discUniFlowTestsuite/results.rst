.. note::

   This snapshot holds 2 of the 6 cases of the full sweep (a ``--smoke`` run). Run the full sweep and refresh the snapshot (:ref:`refresh-the-results`) for all of them.

.. list-table::
   :header-rows: 1
   :widths: auto

   * - ``method``
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
     - Serial
     - n100x60
     - 6000
     - 0.03037
     - 5.551e-17
     - 3.675e-19
     - 0.002401
     - 4.909
     - 1200
   * - isoAdvector
     - Serial
     - n100x60
     - 6000
     - 0.02253
     - 3.886e-16
     - 0
     - 0.0006355
     - 2.806
     - 1200
