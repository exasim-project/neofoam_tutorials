"""``setAlphaPlane``: OpenFOAM setAlphaField's ``type plane`` as a NeoFOAM preprocess tool.

NeoFOAM's ``setAlphaField`` tool knows the ``sphere`` and ``cylinder`` functions only.
This tool reads the same ``system/setAlphaFieldDict`` with OpenFOAM's plane entries and
sets the field to the ``cutCellIso`` volume fraction of the plane function
``normal . (p - origin)`` (positive on the side the normal points to), with NeoFOAM's
cut (:func:`neofoam.preprocess.cut_cell_iso.volume_fraction`, exact for a plane)::

    field   alpha.water;
    type    plane;
    origin  (0 0 0.1345);
    normal  (0 0 -1);       // alpha 1 below z = 0.1345

In ``system/preprocess.yaml``: ``{tool: setAlphaPlane, depends_on: [blockMesh]}``.
Registered through the ``neofoam.plugins`` entry point (pyproject).
"""

# NB: no ``from __future__ import annotations`` -- the tool's step config is the live
# annotation of its build function.

from pathlib import Path
from typing import Any, Literal

from neofoam.io import OF, BaseConfig, IOStrategy
from pydantic import BaseModel, field_validator


class SetAlphaPlaneStep(BaseModel):
    """Set a volume fraction field from the plane of ``system/setAlphaFieldDict``."""

    tool: Literal["setAlphaPlane"]
    dict_file: str = "system/setAlphaFieldDict"


@IOStrategy(OF("system/setAlphaFieldDict"))
class SetAlphaPlaneDictConfig(BaseConfig):  # type: ignore[misc]
    field: str
    type: Literal["plane"]
    origin: list[float]
    normal: list[float]

    @field_validator("field", mode="before")
    @classmethod
    def _unquote(cls, value: Any) -> Any:
        return value.strip('"') if isinstance(value, str) else value

    @field_validator("origin", "normal", mode="before")
    @classmethod
    def _parse_vector(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [float(v) for v in value.strip().strip("()").split()]
        return value


def set_alpha_plane(mesh: Any, config: SetAlphaPlaneDictConfig) -> None:
    """Write the start time's field (run from the case, the field must exist there)."""
    import numpy as np
    import pybFoam as pyf
    from neofoam.preprocess.cut_cell_iso import PolyMeshTopology, volume_fraction

    topology = PolyMeshTopology.read(Path("."))
    normal = np.asarray(config.normal, dtype=float)
    normal /= np.linalg.norm(normal)
    f = (topology.points - np.asarray(config.origin, dtype=float)) @ normal
    field = pyf.volScalarField.read_field(mesh, config.field, False)
    np.asarray(field.internalField())[:] = volume_fraction(topology, f, np.asarray(mesh.V()))
    field.correctBoundaryConditions()
    pyf.write(field)


def _register() -> None:
    from neofoam.framework.initialization import InitStep
    from neofoam.framework.tools import Tool
    from neofoam.tools.registry import register_tool

    tool = Tool("setAlphaPlane", consumes_mesh=True)

    @tool.build  # type: ignore[untyped-decorator]
    def _build(cfg: SetAlphaPlaneStep) -> list[InitStep]:
        def run(ctx: dict[str, Any]) -> Any:
            mesh = ctx["_prev_mesh"]
            set_alpha_plane(mesh, SetAlphaPlaneDictConfig.load(case_dir=cfg.dict_file))
            return mesh

        return [InitStep(name="preprocess.setAlphaPlane", initializer=run)]

    register_tool(tool)


_register()
