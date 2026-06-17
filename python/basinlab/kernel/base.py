"""
Kernel protocol contracts for BasinLab execution backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PersistentKernel(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def inspect_namespace(self) -> Dict[str, Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self) -> Dict[str, Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def restore(self, snapshot: Dict[str, Dict[str, str]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
