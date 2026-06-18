"""
Package-layout and clean-environment tests for EphUX local wrappers.
"""

import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def test_import_ephux_local_resolves_to_canonical_runtime():
    sys.path.insert(0, str(ROOT))
    import ephux_local  # type: ignore

    assert ephux_local.EphuxLocalService.__module__.startswith("python.ephux_local.")
    assert ephux_local.LocalServiceConfig.__module__.startswith("python.ephux_local.")


def test_clean_temp_virtualenv_runs_ephux_acceptance():
    with tempfile.TemporaryDirectory() as td:
        venv_dir = Path(td) / "venv"
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)
        python_exe = _venv_python(venv_dir)

        install = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "-q", "-e", f"{ROOT}[dev]"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert install.returncode == 0, install.stderr

        artifact_dir = Path(td) / "artifacts"
        run_acceptance = subprocess.run(
            [
                str(python_exe),
                "-m",
                "ephux_local.acceptance",
                "--all",
                "--artifact-dir",
                str(artifact_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert run_acceptance.returncode == 0, run_acceptance.stderr
        summary = json.loads((artifact_dir / "ephux-local-acceptance-summary.json").read_text(encoding="utf-8"))
        assert summary["passed"] is True
