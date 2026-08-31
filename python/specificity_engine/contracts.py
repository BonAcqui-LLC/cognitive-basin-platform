"""
Typed contracts for deterministic specificity measurement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


PathPart = str | int


class ComparisonMode(str, Enum):
    """Supported deterministic feature comparators."""

    EXACT = "EXACT"
    NUMERIC = "NUMERIC"
    SET = "SET"
    SEQUENCE = "SEQUENCE"


@dataclass(frozen=True)
class TargetFeature:
    """One target-relevant feature and where it appears in each record."""

    name: str
    reference_path: Tuple[PathPart, ...]
    encoded_path: Tuple[PathPart, ...]
    weight: float = 1.0
    comparison: ComparisonMode = ComparisonMode.EXACT
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("feature name must not be empty")
        if not self.reference_path:
            raise ValueError(f"{self.name}: reference_path must not be empty")
        if not self.encoded_path:
            raise ValueError(f"{self.name}: encoded_path must not be empty")
        if self.weight <= 0:
            raise ValueError(f"{self.name}: weight must be positive")
        if self.tolerance < 0:
            raise ValueError(f"{self.name}: tolerance must be non-negative")

    def to_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "reference_path": list(self.reference_path),
            "encoded_path": list(self.encoded_path),
            "weight": self.weight,
            "comparison": self.comparison.value,
            "tolerance": self.tolerance,
        }


@dataclass(frozen=True)
class SpecificityTarget:
    """The explicit feature set relevant to one measurement purpose."""

    target_id: str
    purpose: str
    features: Tuple[TargetFeature, ...]

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError("target_id must not be empty")
        if not self.purpose.strip():
            raise ValueError("target purpose must not be empty")
        if not self.features:
            raise ValueError("a specificity target requires at least one feature")
        names = [feature.name for feature in self.features]
        if len(set(names)) != len(names):
            raise ValueError("target feature names must be unique")

    def to_record(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "purpose": self.purpose,
            "features": [feature.to_record() for feature in self.features],
        }


@dataclass(frozen=True)
class Representation:
    """A full developmental record and the encoded form being evaluated."""

    representation_id: str
    target: SpecificityTarget
    full_record: Any
    geometric_form: Any
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty")


@dataclass(frozen=True)
class FeatureMeasurement:
    """Immutable result for one target feature."""

    name: str
    comparison: ComparisonMode
    weight: float
    score: float
    reference_hash: str
    observed_hash: str
    reference_missing: bool = False
    observed_missing: bool = False

    def to_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "comparison": self.comparison.value,
            "weight": self.weight,
            "score": self.score,
            "reference_hash": self.reference_hash,
            "observed_hash": self.observed_hash,
            "reference_missing": self.reference_missing,
            "observed_missing": self.observed_missing,
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "FeatureMeasurement":
        return cls(
            name=str(payload["name"]),
            comparison=ComparisonMode(str(payload["comparison"])),
            weight=float(payload["weight"]),
            score=float(payload["score"]),
            reference_hash=str(payload["reference_hash"]),
            observed_hash=str(payload["observed_hash"]),
            reference_missing=bool(payload.get("reference_missing", False)),
            observed_missing=bool(payload.get("observed_missing", False)),
        )


@dataclass(frozen=True)
class MeasurementReceipt:
    """Hash-addressed GSR/NGR result computed once from target-relevant inputs."""

    receipt_id: str
    algorithm_version: str
    representation_id: str
    target_id: str
    input_hash: str
    gsr: float
    ngr: float
    feature_measurements: Tuple[FeatureMeasurement, ...]
    provenance: Tuple[str, ...] = ()

    def to_record(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "algorithm_version": self.algorithm_version,
            "representation_id": self.representation_id,
            "target_id": self.target_id,
            "input_hash": self.input_hash,
            "gsr": self.gsr,
            "ngr": self.ngr,
            "feature_measurements": [
                measurement.to_record() for measurement in self.feature_measurements
            ],
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_record(cls, payload: Dict[str, Any]) -> "MeasurementReceipt":
        return cls(
            receipt_id=str(payload["receipt_id"]),
            algorithm_version=str(payload["algorithm_version"]),
            representation_id=str(payload["representation_id"]),
            target_id=str(payload["target_id"]),
            input_hash=str(payload["input_hash"]),
            gsr=float(payload["gsr"]),
            ngr=float(payload["ngr"]),
            feature_measurements=tuple(
                FeatureMeasurement.from_record(item)
                for item in payload.get("feature_measurements", [])
            ),
            provenance=tuple(str(item) for item in payload.get("provenance", [])),
        )
