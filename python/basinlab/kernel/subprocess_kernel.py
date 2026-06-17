"""
Persistent subprocess-backed BasinLab kernel.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict

from .base import PersistentKernel


class SubprocessKernel(PersistentKernel):
    def __init__(self) -> None:
        self._proc: subprocess.Popen[str] | None = None
        self._responses: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._reader: threading.Thread | None = None
        self.pid: int | None = None
        self.repo_root = Path(__file__).resolve().parents[3]

    def start(self) -> None:
        if self._proc and self._proc.poll() is None:
            return
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "python.basinlab.kernel.worker"],
            cwd=str(self.repo_root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._stdout_reader, daemon=True)
        self._reader.start()
        response = self._request({"op": "start"}, timeout_s=2.0)
        self.pid = response.get("pid")

    def _stdout_reader(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for line in self._proc.stdout:
            if not line.strip():
                continue
            try:
                self._responses.put(json.loads(line))
            except json.JSONDecodeError as exc:
                self._responses.put({"ok": False, "error": f"Invalid worker JSON: {exc}"})

    def _ensure_running(self) -> None:
        self.start()
        if self._proc is None or self._proc.poll() is not None:
            raise RuntimeError("BasinLab kernel is not running")

    def _request(self, payload: Dict[str, Any], timeout_s: float = 5.0) -> Dict[str, Any]:
        self._ensure_running()
        assert self._proc is not None and self._proc.stdin is not None
        self._proc.stdin.write(json.dumps(payload) + "\n")
        self._proc.stdin.flush()
        try:
            response = self._responses.get(timeout=timeout_s)
        except queue.Empty as exc:
            self._terminate()
            raise TimeoutError(f"BasinLab kernel timed out waiting for {payload['op']}") from exc
        if not response.get("ok", False):
            raise RuntimeError(response.get("error", "Unknown worker failure"))
        return response

    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        return self._request({"op": "execute", "code": code}, timeout_s=timeout_s)

    def inspect_namespace(self) -> Dict[str, Dict[str, str]]:
        response = self._request({"op": "inspect_namespace"}, timeout_s=2.0)
        return response.get("namespace_summary", {})

    def snapshot(self) -> Dict[str, Dict[str, str]]:
        response = self._request({"op": "snapshot"}, timeout_s=2.0)
        return response.get("snapshot", {})

    def restore(self, snapshot: Dict[str, Dict[str, str]]) -> None:
        self._request({"op": "restore", "snapshot": snapshot}, timeout_s=2.0)

    def reset(self) -> None:
        self._request({"op": "reset"}, timeout_s=2.0)

    def _terminate(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.kill()
            self._proc.wait(timeout=2.0)
        self._proc = None
        self.pid = None

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._request({"op": "close"}, timeout_s=2.0)
            except Exception:
                self._terminate()
            else:
                self._proc.wait(timeout=2.0)
                self._proc = None
                self.pid = None

