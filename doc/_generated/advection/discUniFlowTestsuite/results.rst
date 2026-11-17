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
     - CPU
     - n100x60
     - 6000
     - 0.03037
     - 5.551e-17
     - 3.675e-19
     - 0.0025
     - 5.03
     - 1200
   * - MULES
     - GPU
     - n100x60
     - 6000
     - 0.03037
     - 0
     - 3.78e-19
     - 0.0008245
     - 3.035
     - 1200
   * - MULES
     - Serial
     - n100x60
     - 6000
     - 0.03037
     - 5.551e-17
     - 3.675e-19
     - 0.002407
     - 4.886
     - 1200
   * - isoAdvector
     - CPU
     - n100x60
     - 6000
     - 0.02253
     - 3.886e-16
     - 0
     - 0.0006691
     - 2.797
     - 1200
   * - isoAdvector
     - GPU
     - n100x60
     - 6000
     - 0.02253
     - 3.886e-16
     - 0
     - 0.000956
     - 3.227
     - 1200
   * - isoAdvector
     - Serial
     - n100x60
     - 6000
     - 0.02253
     - 3.886e-16
     - 0
     - 0.0006275
     - 2.733
     - 1200
