"""
Portable virtual-environment interpreter helpers for tests.
"""

from __future__ import annotations

import os
from pathlib import Path


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
