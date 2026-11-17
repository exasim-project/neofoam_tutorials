# Configuration file for the Sphinx documentation builder (``pixi run docs``).
#
# The benchmark results come from the committed snapshot in _generated/
# (_scripts/sync_results.py copies new runs there); the tables are rendered here, at
# build time, so a plain ``sphinx-build -W -b html doc doc/_build/html`` builds too.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_scripts"))

import sync_results  # noqa: E402

sync_results.render_all()

project = "neofoam_verification"
copyright = "2025, NeoFOAM authors"
author = "NeoFOAM authors"

extensions = [
    "sphinxcontrib.mermaid",
]

# _generated/ holds include files (the benchmark tables), not pages
exclude_patterns = ["_build", "_generated", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "NeoFOAM verification"
html_static_path = ["_static"]
