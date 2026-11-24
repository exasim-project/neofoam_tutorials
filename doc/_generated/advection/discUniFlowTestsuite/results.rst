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
     - 1.11e-16
     - 3.675e-19
     - 0.002498
     - 5.053
     - 1200
   * - MULES
     - GPU
     - n100x60
     - 6000
     - 0.03037
     - 3.886e-16
     - 7.956e-19
     - 0.0008285
     - 3.13
     - 1200
   * - MULES
     - Serial
     - n100x60
     - 6000
     - 0.03037
     - 1.11e-16
     - 3.675e-19
     - 0.002411
     - 4.958
     - 1200
   * - isoAdvector
     - CPU
     - n100x60
     - 6000
     - 0.02253
     - 4.718e-16
     - 0
     - 0.000674
     - 2.879
     - 1200
   * - isoAdvector
     - GPU
     - n100x60
     - 6000
     - 0.02253
     - 4.718e-16
     - 0
     - 0.000969
     - 3.314
     - 1200
   * - isoAdvector
     - Serial
     - n100x60
     - 6000
     - 0.02253
     - 4.718e-16
     - 0
     - 0.0006328
     - 2.856
     - 1200
