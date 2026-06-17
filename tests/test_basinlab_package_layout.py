"""
Package-layout and clean-environment tests for BasinLab.
"""

import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / "Scripts" / "python.exe"


def test_import_basinlab_resolves_to_canonical_runtime():
    sys.path.insert(0, str(ROOT))
    import basinlab  # type: ignore

    assert basinlab.BasinLabSession.__module__.startswith("python.basinlab.")
    assert basinlab.SessionStore.__module__.startswith("python.basinlab.")


def test_clean_temp_virtualenv_behaves_like_local_checkout():
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

        run_all = subprocess.run(
            [
                str(python_exe),
                "-m",
                "basinlab.cli.main",
                "--store-dir",
                str(Path(td) / "store"),
                "run-all",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert run_all.returncode == 0, run_all.stderr
        payload = json.loads(run_all.stdout)
        assert payload["passed"] is True
        first_session = payload["session_ids"][0]

        inspect = subprocess.run(
            [
                str(python_exe),
                "-m",
                "basinlab.cli.main",
                "--store-dir",
                str(Path(td) / "store"),
                "inspect",
                first_session,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        replay = subprocess.run(
            [
                str(python_exe),
                "-m",
                "basinlab.cli.main",
                "--store-dir",
                str(Path(td) / "store"),
                "replay",
                first_session,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert inspect.returncode == 0, inspect.stderr
        assert replay.returncode == 0, replay.stderr
        assert json.loads(inspect.stdout)["session_id"] == first_session
        assert json.loads(replay.stdout)["replay_hash"]
