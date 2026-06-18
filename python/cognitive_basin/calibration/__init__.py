"""
Calibration tracking across predictive cognition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
class CalibrationBucket:
    label: str
    predicted_mean: float
    observed_mean: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "predicted_mean": self.predicted_mean,
            "observed_mean": self.observed_mean,
        }


@dataclass
class CalibrationReceipt:
    brier_score: float
    expected_calibration_error: float
    false_support_rate: float
    false_hold_rate: float
    missed_contradiction_rate: float
    overconfidence_rate: float
    underconfidence_rate: float
    buckets: List[CalibrationBucket] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "brier_score": self.brier_score,
            "expected_calibration_error": self.expected_calibration_error,
            "false_support_rate": self.false_support_rate,
            "false_hold_rate": self.false_hold_rate,
            "missed_contradiction_rate": self.missed_contradiction_rate,
            "overconfidence_rate": self.overconfidence_rate,
            "underconfidence_rate": self.underconfidence_rate,
            "buckets": _record(self.buckets),
        }


class CalibrationTracker:
    def assess(self, confidences: List[float], outcomes: List[float]) -> CalibrationReceipt:
        if not confidences or not outcomes:
            return CalibrationReceipt(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
        pairs = list(zip(confidences, outcomes))
        brier = sum((confidence - outcome) ** 2 for confidence, outcome in pairs) / len(pairs)
        predicted_mean = sum(confidences) / len(confidences)
        observed_mean = sum(outcomes) / len(outcomes)
        ece = abs(predicted_mean - observed_mean)
        overconfidence = sum(1 for confidence, outcome in pairs if confidence > 0.75 and outcome < 0.5) / len(pairs)
        underconfidence = sum(1 for confidence, outcome in pairs if confidence < 0.4 and outcome > 0.5) / len(pairs)
        return CalibrationReceipt(
            round(brier, 4),
            round(ece, 4),
            round(sum(1 for outcome in outcomes if outcome == 0.0) / len(outcomes), 4),
            round(sum(1 for outcome in outcomes if outcome < 1.0) / len(outcomes), 4),
            0.0,
            round(overconfidence, 4),
            round(underconfidence, 4),
            [CalibrationBucket("all", round(predicted_mean, 4), round(observed_mean, 4))],
        )


__all__ = ["CalibrationBucket", "CalibrationReceipt", "CalibrationTracker"]
