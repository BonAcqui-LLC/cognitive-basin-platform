"""
Clean-environment package-layout checks for aggregate acceptance wrappers.
"""

import json
import subprocess
import tempfile
import venv
from pathlib import Path
from tools.test_support.venv_paths import venv_python

ROOT = Path(__file__).parent.parent


def test_clean_temp_virtualenv_runs_aggregate_acceptance():
    with tempfile.TemporaryDirectory() as td:
        venv_dir = Path(td) / "venv"
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)
        python_exe = venv_python(venv_dir)

        install = subprocess.run(
            [str(python_exe), "-m", "pip", "install", "-q", "-e", f"{ROOT}[dev]"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert install.returncode == 0, install.stderr

        wrapper_imports = subprocess.run(
            [
                str(python_exe),
                "-c",
                (
                    "import basinlab, cognitive_basin, ephux_local, evaluation_lab, "
                    "natural_math_lab, provider_lab, sandbox_lab; "
                    "print(basinlab.BasinLabSession.__module__); "
                    "print(ephux_local.EphuxLocalService.__module__); "
                    "print(evaluation_lab.run_evaluation_suite.__module__); "
                    "print(natural_math_lab.run_parameter_sweep.__module__)"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert wrapper_imports.returncode == 0, wrapper_imports.stderr
        stdout = wrapper_imports.stdout
        assert "python.basinlab." in stdout
        assert "python.ephux_local." in stdout
        assert "python.evaluation_lab." in stdout
        assert "python.natural_math_lab." in stdout

        artifact_dir = Path(td) / "artifacts"
        run_acceptance = subprocess.run(
            [
                str(python_exe),
                "-m",
                "cognitive_basin.acceptance",
                "--all",
                "--artifact-dir",
                str(artifact_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert run_acceptance.returncode == 0, run_acceptance.stderr
        summary = json.loads((artifact_dir / "combined-acceptance-manifest.json").read_text(encoding="utf-8"))
        assert summary["passed"] is True
        assert "evaluation_lab" in summary["suites"]
        assert "natural_math_lab" in summary["suites"]
        assert "memory_governance" in summary["suites"]
