.. note::

   This snapshot holds 2 of the 24 cases of the full sweep (a ``--smoke`` run). Run the full sweep and refresh the snapshot (:ref:`refresh-the-results`) for all of them.

.. list-table::
   :header-rows: 1
   :widths: auto

   * - ``executor``
     - ``method``
     - ``mesh``
     - ``nCells``
     - ``LNormalInf``
     - ``LNormal1``
     - ``LCentreInf``
     - ``LCentre1``
     - ``k1``
     - ``wall_s``
   * - Serial
     - gradAlpha
     - n8
     - 64
     - 0.02986
     - 0.003875
     - 0.02965
     - 0.01505
     - 4.78e-05
     - 0.2463
   * - Serial
     - gradAlpha
     - n16
     - 256
     - 0.0142
     - 0.002682
     - 0.007618
     - 0.003825
     - 6.421e-05
     - 0.208
