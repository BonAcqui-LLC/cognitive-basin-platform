"""
Prediction, residual, and surprise accounting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from python.cognitive_basin.consciousness.common import now_ts
from python.cognitive_basin.world_model import WorldObservation


def _record(value: Any) -> Any:
    if hasattr(value, "to_record"):
        return value.to_record()
    if isinstance(value, list):
        return [_record(item) for item in value]
    if isinstance(value, dict):
        return {key: _record(item) for key, item in value.items()}
    return value


@dataclass
class PredictionID:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class PredictionTarget:
    entity_id: str
    property_name: str

    def to_record(self) -> Dict[str, Any]:
        return {"entity_id": self.entity_id, "property_name": self.property_name}


@dataclass
class PredictionHorizon:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class PredictionDistribution:
    expected_value: Any
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    confidence: float = 0.5

    def to_record(self) -> Dict[str, Any]:
        return {
            "expected_value": self.expected_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence": self.confidence,
        }


@dataclass
class PredictionAssumption:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PredictionEvidence:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class PredictionOutcome:
    observation_id: str
    observed_value: Any
    observed_at: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "observed_value": self.observed_value,
            "observed_at": self.observed_at,
        }


@dataclass
class ResidualMagnitude:
    value: float

    def to_record(self) -> float:
        return self.value


@dataclass
class ResidualDirection:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class SurpriseSource:
    value: str

    def to_record(self) -> str:
        return self.value


@dataclass
class PredictionResidual:
    prediction_id: str
    residual_type: str
    magnitude: ResidualMagnitude
    direction: ResidualDirection
    expected_value: Any
    observed_value: Any
    surprise_source: SurpriseSource

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "residual_type": self.residual_type,
            "magnitude": self.magnitude.to_record(),
            "direction": self.direction.to_record(),
            "expected_value": self.expected_value,
            "observed_value": self.observed_value,
            "surprise_source": self.surprise_source.to_record(),
        }


@dataclass
class ExpectedSurprise:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class UnexpectedSurprise:
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"detail": self.detail}


@dataclass
class SurpriseAssessment:
    state: str
    detail: str

    def to_record(self) -> Dict[str, Any]:
        return {"state": self.state, "detail": self.detail}


@dataclass
class SurpriseResponse:
    actions: List[str]

    def to_record(self) -> Dict[str, Any]:
        return {"actions": list(self.actions)}


@dataclass
class ResidualHistory:
    residuals: List[PredictionResidual] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {"residuals": _record(self.residuals)}


@dataclass
class PredictionError:
    residual: PredictionResidual
    actual_observation: Dict[str, Any]

    def to_record(self) -> Dict[str, Any]:
        return {"residual": self.residual.to_record(), "actual_observation": dict(self.actual_observation)}


@dataclass
class PredictionCalibration:
    brier_score: float
    calibration_bucket: str
    expected_calibration_error: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "brier_score": self.brier_score,
            "calibration_bucket": self.calibration_bucket,
            "expected_calibration_error": self.expected_calibration_error,
        }


@dataclass
class PredictionRevision:
    prediction_id: str
    reason: str
    prior_confidence: float
    new_confidence: float

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "reason": self.reason,
            "prior_confidence": self.prior_confidence,
            "new_confidence": self.new_confidence,
        }


@dataclass
class Prediction:
    prediction_id: PredictionID
    target: PredictionTarget
    horizon: PredictionHorizon
    distribution: PredictionDistribution
    assumptions: List[PredictionAssumption]
    evidence: List[PredictionEvidence]
    verification_method: str
    expiry: float
    source_model: str
    actual_observation: Dict[str, Any] = field(default_factory=dict)
    error: Dict[str, Any] = field(default_factory=dict)
    calibration_effect: Dict[str, Any] = field(default_factory=dict)
    status: str = "UNRESOLVED"

    def to_record(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id.to_record(),
            "target": self.target.to_record(),
            "horizon": self.horizon.to_record(),
            "distribution": self.distribution.to_record(),
            "assumptions": _record(self.assumptions),
            "evidence": _record(self.evidence),
            "verification_method": self.verification_method,
            "expiry": self.expiry,
            "source_model": self.source_model,
            "actual_observation": dict(self.actual_observation),
            "error": dict(self.error),
            "calibration_effect": dict(self.calibration_effect),
            "status": self.status,
        }


@dataclass
class PredictionReceipt:
    predictions: List[Prediction]
    verified: List[str]
    expired: List[str]
    residuals: List[PredictionResidual]
    surprise: SurpriseAssessment
    response: SurpriseResponse
    calibration: PredictionCalibration
    revisions: List[PredictionRevision]

    def to_record(self) -> Dict[str, Any]:
        return {
            "predictions": _record(self.predictions),
            "verified": list(self.verified),
            "expired": list(self.expired),
            "residuals": _record(self.residuals),
            "surprise": self.surprise.to_record(),
            "response": self.response.to_record(),
            "calibration": self.calibration.to_record(),
            "revisions": _record(self.revisions),
        }


class PredictionEngine:
    def __init__(self) -> None:
        self.predictions: Dict[str, Prediction] = {}
        self.history = ResidualHistory()

    def create_prediction(
        self,
        *,
        entity_id: str,
        property_name: str,
        expected_value: Any,
        horizon: str,
        source_model: str,
        confidence: float,
        assumptions: List[str],
        evidence: List[str],
        verification_method: str,
        expiry: float,
    ) -> Prediction:
        prediction = Prediction(
            prediction_id=PredictionID(f"prediction-{len(self.predictions) + 1:04d}"),
            target=PredictionTarget(entity_id, property_name),
            horizon=PredictionHorizon(horizon),
            distribution=PredictionDistribution(expected_value=expected_value, confidence=confidence),
            assumptions=[PredictionAssumption(item) for item in assumptions],
            evidence=[PredictionEvidence(item) for item in evidence],
            verification_method=verification_method,
            expiry=expiry,
            source_model=source_model,
        )
        self.predictions[prediction.prediction_id.value] = prediction
        return prediction

    def _residual_for(self, prediction: Prediction, observation: WorldObservation) -> PredictionResidual:
        expected = prediction.distribution.expected_value
        observed = observation.value
        if isinstance(expected, (int, float)) and isinstance(observed, (int, float)):
            magnitude = abs(float(observed) - float(expected))
            direction = "HIGHER" if observed > expected else "LOWER" if observed < expected else "MATCH"
            residual_type = "NUMERICAL_ERROR" if magnitude > 0 else "NONE"
        else:
            magnitude = 0.0 if observed == expected else 1.0
            direction = "MATCH" if observed == expected else "MISMATCH"
            residual_type = "CATEGORICAL_MISMATCH" if observed != expected else "NONE"
        if observation.property_name != prediction.target.property_name:
            residual_type = "SCOPE_ERROR"
            magnitude = 1.0
            direction = "MISMATCH"
        return PredictionResidual(
            prediction_id=prediction.prediction_id.value,
            residual_type=residual_type,
            magnitude=ResidualMagnitude(magnitude),
            direction=ResidualDirection(direction),
            expected_value=expected,
            observed_value=observed,
            surprise_source=SurpriseSource("observation-mismatch" if residual_type != "NONE" else "verification"),
        )

    def verify(self, observations: List[WorldObservation], *, now: float | None = None) -> PredictionReceipt:
        current = now_ts() if now is None else now
        verified: List[str] = []
        expired: List[str] = []
        residuals: List[PredictionResidual] = []
        revisions: List[PredictionRevision] = []
        by_target = {(item.entity_id, item.property_name): item for item in observations}
        matched_keys: set[tuple[str, str]] = set()
        for prediction in self.predictions.values():
            key = (prediction.target.entity_id, prediction.target.property_name)
            if key in by_target:
                matched_keys.add(key)
                observation = by_target[key]
                residual = self._residual_for(prediction, observation)
                prediction.actual_observation = observation.to_record()
                prediction.error = residual.to_record() if residual.residual_type != "NONE" else {}
                prediction.status = "VERIFIED" if residual.residual_type == "NONE" else "FALSIFIED"
                residuals.append(residual)
                verified.append(prediction.prediction_id.value)
                if residual.residual_type != "NONE":
                    prior = prediction.distribution.confidence
                    prediction.distribution.confidence = max(0.05, prior - 0.2)
                    revisions.append(
                        PredictionRevision(
                            prediction_id=prediction.prediction_id.value,
                            reason=residual.residual_type,
                            prior_confidence=prior,
                            new_confidence=prediction.distribution.confidence,
                        )
                    )
            elif prediction.expiry <= current and prediction.status == "UNRESOLVED":
                prediction.status = "UNRESOLVED"
                expired.append(prediction.prediction_id.value)
                residuals.append(
                    PredictionResidual(
                        prediction_id=prediction.prediction_id.value,
                        residual_type="MISSING_PREDICTED_EVENT",
                        magnitude=ResidualMagnitude(1.0),
                        direction=ResidualDirection("MISSING"),
                        expected_value=prediction.distribution.expected_value,
                        observed_value=None,
                        surprise_source=SurpriseSource("missing-event"),
                    )
                )
        for key, observation in by_target.items():
            if key in matched_keys:
                continue
            residuals.append(
                PredictionResidual(
                    prediction_id="unexpected-observation",
                    residual_type="UNEXPECTED_EVENT",
                    magnitude=ResidualMagnitude(1.0),
                    direction=ResidualDirection("UNEXPECTED"),
                    expected_value=None,
                    observed_value=observation.value,
                    surprise_source=SurpriseSource("unexpected-event"),
                )
            )
        self.history.residuals.extend(residuals)
        surprise_level = "EXPECTED"
        surprise_detail = "predictions matched or remained unresolved"
        if any(item.residual_type not in {"NONE"} for item in residuals):
            surprise_level = "UNEXPECTED"
            surprise_detail = "prediction discrepancies detected"
        calibration = self._calibration()
        return PredictionReceipt(
            predictions=list(self.predictions.values()),
            verified=verified,
            expired=expired,
            residuals=residuals,
            surprise=SurpriseAssessment(surprise_level, surprise_detail),
            response=SurpriseResponse(
                [
                    "attention_shift",
                    "world_model_revision",
                    "rigor_review",
                ]
                if surprise_level == "UNEXPECTED"
                else ["continue"]
            ),
            calibration=calibration,
            revisions=revisions,
        )

    def _calibration(self) -> PredictionCalibration:
        scored = [item for item in self.predictions.values() if item.status in {"VERIFIED", "FALSIFIED"}]
        if not scored:
            return PredictionCalibration(0.0, "EMPTY", 0.0)
        squared = []
        for item in scored:
            target = 1.0 if item.status == "VERIFIED" else 0.0
            squared.append((item.distribution.confidence - target) ** 2)
        brier = sum(squared) / len(squared)
        bucket = "WELL_CALIBRATED" if brier <= 0.15 else "OVERCONFIDENT"
        ece = abs(sum(item.distribution.confidence for item in scored) / len(scored) - sum(1.0 if item.status == "VERIFIED" else 0.0 for item in scored) / len(scored))
        return PredictionCalibration(round(brier, 4), bucket, round(ece, 4))


__all__ = [
    "ExpectedSurprise",
    "Prediction",
    "PredictionAssumption",
    "PredictionCalibration",
    "PredictionDistribution",
    "PredictionEngine",
    "PredictionError",
    "PredictionEvidence",
    "PredictionHorizon",
    "PredictionID",
    "PredictionOutcome",
    "PredictionReceipt",
    "PredictionResidual",
    "PredictionRevision",
    "PredictionTarget",
    "ResidualDirection",
    "ResidualHistory",
    "ResidualMagnitude",
    "SurpriseAssessment",
    "SurpriseResponse",
    "SurpriseSource",
    "UnexpectedSurprise",
]
