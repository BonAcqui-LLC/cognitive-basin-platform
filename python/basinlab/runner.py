"""
Execution runner abstraction and auditable receipts.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Protocol

from .kernel.subprocess_kernel import KernelCrashedError, KernelProtocolError, SubprocessKernel


ENFORCED = "ENFORCED"
BEST_EFFORT = "BEST_EFFORT"
UNSUPPORTED = "UNSUPPORTED"


@dataclass
class RunnerReceipt:
    runner_type: str
    policy_version: str
    process_identity: str
    workspace: str
    enforced_restrictions: List[str] = field(default_factory=list)
    best_effort_restrictions: List[str] = field(default_factory=list)
    unsupported_restrictions: List[str] = field(default_factory=list)
    restriction_classification: Dict[str, str] = field(default_factory=dict)
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0
    timeout_s: float = 0.0
    memory_result: str = "UNKNOWN"
    filesystem_changes: List[str] = field(default_factory=list)
    network_result: str = "UNKNOWN"
    rejected_actions: List[str] = field(default_factory=list)
    exit_code: int | None = None
    output_hash: str = ""
    artifact_hashes: Dict[str, str] = field(default_factory=dict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "runner_type": self.runner_type,
            "policy_version": self.policy_version,
            "process_identity": self.process_identity,
            "workspace": self.workspace,
            "enforced_restrictions": list(self.enforced_restrictions),
            "best_effort_restrictions": list(self.best_effort_restrictions),
            "unsupported_restrictions": list(self.unsupported_restrictions),
            "restriction_classification": dict(self.restriction_classification),
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "timeout_s": self.timeout_s,
            "memory_result": self.memory_result,
            "filesystem_changes": list(self.filesystem_changes),
            "network_result": self.network_result,
            "rejected_actions": list(self.rejected_actions),
            "exit_code": self.exit_code,
            "output_hash": self.output_hash,
            "artifact_hashes": dict(self.artifact_hashes),
        }


class RunnerExecutionError(RuntimeError):
    def __init__(self, message: str, *, receipt: RunnerReceipt, timed_out: bool = False, error_class: str = "") -> None:
        super().__init__(message)
        self.receipt = receipt
        self.timed_out = timed_out
        self.error_class = error_class


class Runner(Protocol):
    kernel: SubprocessKernel | None

    def start(self) -> None:
        ...

    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        ...

    def inspect_namespace(self) -> Dict[str, Dict[str, Any]]:
        ...

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        ...

    def snapshot_with_summary(self) -> Dict[str, Any]:
        ...

    def restore(self, snapshot: Dict[str, Dict[str, Any]]) -> None:
        ...

    def load_bindings(self, bindings: Dict[str, Dict[str, Any]]) -> None:
        ...

    def reset(self) -> None:
        ...

    def restart(self) -> None:
        ...

    def close(self) -> None:
        ...


def default_restriction_classification() -> Dict[str, str]:
    return {
        "separate_process": ENFORCED,
        "restricted_builtins": ENFORCED,
        "import_block": ENFORCED,
        "subprocess_block": ENFORCED,
        "network_block": ENFORCED,
        "filesystem_mutation_block": ENFORCED,
        "timeout": BEST_EFFORT,
        "memory_limit": BEST_EFFORT,
        "orphan_cleanup": BEST_EFFORT,
        "network_egress_runtime": UNSUPPORTED,
        "workspace_write_confinement": BEST_EFFORT,
        "process_isolation": UNSUPPORTED,
    }


def build_receipt(*, runner_type: str, workspace: str, timeout_s: float, start_ts: float, end_ts: float, output_payload: Dict[str, Any], pid: int | None, rejected_actions: List[str] | None = None, exit_code: int | None = 0) -> RunnerReceipt:
    classification = default_restriction_classification()
    output_hash = hashlib.sha256(json.dumps(output_payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return RunnerReceipt(
        runner_type=runner_type,
        policy_version="basinlab-runner-policy-v1",
        process_identity=str(pid or "unknown"),
        workspace=workspace,
        enforced_restrictions=[name for name, level in classification.items() if level == ENFORCED],
        best_effort_restrictions=[name for name, level in classification.items() if level == BEST_EFFORT],
        unsupported_restrictions=[name for name, level in classification.items() if level == UNSUPPORTED],
        restriction_classification=classification,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        timeout_s=timeout_s,
        memory_result="NOT_MEASURED",
        filesystem_changes=[],
        network_result="NOT_OBSERVED",
        rejected_actions=list(rejected_actions or []),
        exit_code=exit_code,
        output_hash=output_hash,
        artifact_hashes={},
    )


class SubprocessRunner:
    def __init__(self) -> None:
        self.kernel = SubprocessKernel()
        self.workspace = str(Path(__file__).resolve().parents[3])

    def start(self) -> None:
        self.kernel.start()

    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        started = time.time()
        try:
            result = self.kernel.execute(code, timeout_s=timeout_s)
        except TimeoutError as exc:
            receipt = build_receipt(
                runner_type="subprocess",
                workspace=self.workspace,
                timeout_s=timeout_s,
                start_ts=started,
                end_ts=time.time(),
                output_payload={"error": str(exc), "timed_out": True},
                pid=self.kernel.pid,
                rejected_actions=[],
                exit_code=None,
            )
            raise RunnerExecutionError(str(exc), receipt=receipt, timed_out=True, error_class="TimeoutError") from exc
        except (KernelCrashedError, KernelProtocolError) as exc:
            receipt = build_receipt(
                runner_type="subprocess",
                workspace=self.workspace,
                timeout_s=timeout_s,
                start_ts=started,
                end_ts=time.time(),
                output_payload={"error": str(exc)},
                pid=self.kernel.pid,
                rejected_actions=[],
                exit_code=None,
            )
            raise RunnerExecutionError(str(exc), receipt=receipt, error_class=type(exc).__name__) from exc

        receipt = build_receipt(
            runner_type="subprocess",
            workspace=self.workspace,
            timeout_s=timeout_s,
            start_ts=started,
            end_ts=time.time(),
            output_payload=result,
            pid=self.kernel.pid,
            rejected_actions=[],
            exit_code=0 if not result.get("exception_type") else 1,
        )
        result["runner_receipt"] = receipt.to_record()
        return result

    def inspect_namespace(self) -> Dict[str, Dict[str, Any]]:
        return self.kernel.inspect_namespace()

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return self.kernel.snapshot()

    def snapshot_with_summary(self) -> Dict[str, Any]:
        return self.kernel.snapshot_with_summary()

    def restore(self, snapshot: Dict[str, Dict[str, Any]]) -> None:
        self.kernel.restore(snapshot)

    def load_bindings(self, bindings: Dict[str, Dict[str, Any]]) -> None:
        self.kernel.load_bindings(bindings)

    def reset(self) -> None:
        self.kernel.reset()

    def restart(self) -> None:
        self.kernel.restart()

    def close(self) -> None:
        self.kernel.close()

    def simulate_crash_for_test(self) -> None:
        self.kernel.simulate_crash_for_test()

    def send_malformed_message_for_test(self) -> str:
        return self.kernel.send_malformed_message_for_test()

    def protocol_request(self, payload: Dict[str, Any], timeout_s: float = 5.0) -> Dict[str, Any]:
        return self.kernel.protocol_request(payload, timeout_s=timeout_s)

    @property
    def pid(self) -> int | None:
        return self.kernel.pid


class WslRunner(SubprocessRunner):
    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        raise RunnerExecutionError(
            "WSL runner is not configured in this local tranche",
            receipt=build_receipt(
                runner_type="wsl",
                workspace=self.workspace,
                timeout_s=timeout_s,
                start_ts=time.time(),
                end_ts=time.time(),
                output_payload={"error": "WSL runner unavailable"},
                pid=None,
                rejected_actions=["runner-unavailable"],
                exit_code=None,
            ),
            error_class="RunnerUnavailable",
        )


class ContainerRunner(SubprocessRunner):
    def execute(self, code: str, timeout_s: float = 5.0) -> Dict[str, Any]:
        raise RunnerExecutionError(
            "Container runner is not configured in this local tranche",
            receipt=build_receipt(
                runner_type="container",
                workspace=self.workspace,
                timeout_s=timeout_s,
                start_ts=time.time(),
                end_ts=time.time(),
                output_payload={"error": "Container runner unavailable"},
                pid=None,
                rejected_actions=["runner-unavailable"],
                exit_code=None,
            ),
            error_class="RunnerUnavailable",
        )
