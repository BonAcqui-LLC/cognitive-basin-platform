"""
Anomaly detection across predictive cognition state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class AnomalyClass:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class AnomalyEvidence:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class AnomalySeverity:
    value: float

    def to_record(self) -> float:
        return self.value


@dataclass
class AnomalyBaseline:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class AnomalyResponse:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class AnomalyResolution:
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "detail": self.detail}


@dataclass
class Anomaly:
    anomaly_id: str
    anomaly_class: AnomalyClass
    evidence: List[AnomalyEvidence]
    severity: AnomalySeverity
    baseline: AnomalyBaseline
    response: AnomalyResponse
    resolution: AnomalyResolution

    def to_record(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "anomaly_class": self.anomaly_class.to_record(),
            "evidence": _record(self.evidence),
            "severity": self.severity.to_record(),
            "baseline": self.baseline.to_record(),
            "response": self.response.to_record(),
            "resolution": self.resolution.to_record(),
        }


@dataclass
class AnomalyReceipt:
    anomalies: List[Anomaly]

    def to_record(self) -> Dict[str, Any]:
        return {"anomalies": _record(self.anomalies)}


class AnomalyDetector:
    def detect(
        self,
        *,
        residual_types: List[str],
        contradiction_count: int,
        replay_integrity: bool,
        authority_conflicts: int,
    ) -> AnomalyReceipt:
        anomalies: List[Anomaly] = []
        for residual_type in residual_types:
            if residual_type not in {"NONE"}:
                anomalies.append(
                    Anomaly(
                        anomaly_id=f"anomaly-{len(anomalies) + 1:04d}",
                        anomaly_class=AnomalyClass("MODEL_DRIFT" if "ERROR" in residual_type or "MISMATCH" in residual_type else "NOVEL"),
                        evidence=[AnomalyEvidence(residual_type)],
                        severity=AnomalySeverity(0.8),
                        baseline=AnomalyBaseline("predicted versus observed"),
                        response=AnomalyResponse("investigate and retain uncertainty"),
                        resolution=AnomalyResolution("UNRESOLVED", "requires review"),
                    )
                )
        if contradiction_count:
            anomalies.append(
                Anomaly(
                    anomaly_id=f"anomaly-{len(anomalies) + 1:04d}",
                    anomaly_class=AnomalyClass("CONTRADICTORY"),
                    evidence=[AnomalyEvidence(f"contradictions={contradiction_count}")],
                    severity=AnomalySeverity(0.9),
                    baseline=AnomalyBaseline("non-contradictory baseline"),
                    response=AnomalyResponse("trigger review"),
                    resolution=AnomalyResolution("UNRESOLVED", "contradiction retained"),
                )
            )
        if not replay_integrity:
            anomalies.append(
                Anomaly(
                    anomaly_id=f"anomaly-{len(anomalies) + 1:04d}",
                    anomaly_class=AnomalyClass("REPLAY_MISMATCH"),
                    evidence=[AnomalyEvidence("replay integrity failed")],
                    severity=AnomalySeverity(1.0),
                    baseline=AnomalyBaseline("replay equality"),
                    response=AnomalyResponse("hold and investigate"),
                    resolution=AnomalyResolution("UNRESOLVED", "replay mismatch retained"),
                )
            )
        if authority_conflicts:
            anomalies.append(
                Anomaly(
                    anomaly_id=f"anomaly-{len(anomalies) + 1:04d}",
                    anomaly_class=AnomalyClass("AUTHORITY_MISMATCH"),
                    evidence=[AnomalyEvidence(f"authority conflicts={authority_conflicts}")],
                    severity=AnomalySeverity(0.7),
                    baseline=AnomalyBaseline("explicit authority path"),
                    response=AnomalyResponse("request review"),
                    resolution=AnomalyResolution("UNRESOLVED", "authority mismatch retained"),
                )
            )
        return AnomalyReceipt(anomalies)


__all__ = [
    "Anomaly",
    "AnomalyBaseline",
    "AnomalyClass",
    "AnomalyDetector",
    "AnomalyEvidence",
    "AnomalyReceipt",
    "AnomalyResolution",
    "AnomalyResponse",
    "AnomalySeverity",
]
