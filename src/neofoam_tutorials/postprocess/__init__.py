"""NeoFOAM ``postProcess`` members of the benchmarks (the ``neofoam.plugins`` entry point).

Importing the package registers them, so their ``type`` is valid in a case's
``system/postProcess.yaml``:

* source ``shapeError`` -- ``|alpha - alpha_exact|`` per cell, TwoPhaseFlow's
  ``volumeFractionError`` integrand (``volIntegrate`` it for Eshape);
* source ``startField`` -- a field as written at the start time (the initial mass);
* node ``phaseExtent`` -- the coordinate along a direction of the cells inside a phase
  (``max`` of it: a dam break's surge front);
* node ``hydrostaticError`` -- ``|p - p_hydrostatic|`` over the hydrostatic range;
* node ``change`` -- the largest component of ``|U - U_previous|`` since the table's
  previous evaluation.
"""

from . import change, extent, hydrostatic, volume_fraction

__all__ = ["change", "extent", "hydrostatic", "volume_fraction"]
