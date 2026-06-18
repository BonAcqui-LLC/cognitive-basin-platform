"""
Portable venv path helper tests.
"""

from pathlib import Path

from tools.test_support.venv_paths import venv_python


def test_venv_python_uses_portable_platform_specific_location():
    path = venv_python(Path("venv-root"))
    assert str(path).endswith("Scripts\\python.exe") or str(path).endswith("bin\\python") or str(path).endswith("bin/python")
