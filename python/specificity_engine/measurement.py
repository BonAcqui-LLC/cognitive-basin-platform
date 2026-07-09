"""
Deterministic target-conditioned GSR/NGR measurement.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import (
    ComparisonMode,
    FeatureMeasurement,
    MeasurementReceipt,
    Representation,
    TargetFeature,
)


ALGORITHM_VERSION = "specificity-gsr-0.3.0"
_MISSING = object()


def canonical_json(value: Any) -> str:
    """Return a stable JSON encoding or reject unsupported measurement input."""

    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("specificity inputs must be finite JSON-compatible values") from exc


def _hash_value(value: Any) -> str:
    if value is _MISSING:
        encoded = '"<MISSING>"'
    else:
        encoded = canonical_json(value)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _extract_path(value: Any, path: tuple[str | int, ...]) -> Any:
    current = value
    for part in path:
        if isinstance(part, int):
            if (
                not isinstance(current, Sequence)
                or isinstance(current, (str, bytes, bytearray))
                or part < 0
                or part >= len(current)
            ):
                return _MISSING
            current = current[part]
        else:
            if not isinstance(current, Mapping) or part not in current:
                return _MISSING
            current = current[part]
    return current


def _numeric_score(reference: Any, observed: Any, tolerance: float) -> float:
    if (
        isinstance(reference, bool)
        or isinstance(observed, bool)
        or not isinstance(reference, (int, float))
        or not isinstance(observed, (int, float))
    ):
        return 0.0
    reference_number = float(reference)
    observed_number = float(observed)
    if not math.isfinite(reference_number) or not math.isfinite(observed_number):
        return 0.0
    difference = abs(reference_number - observed_number)
    if difference <= tolerance:
        return 1.0
    scale = max(abs(reference_number), abs(observed_number), 1.0)
    return max(0.0, 1.0 - ((difference - tolerance) / scale))


def _set_score(reference: Any, observed: Any) -> float:
    if (
        not isinstance(reference, Sequence)
        or isinstance(reference, (str, bytes, bytearray))
        or not isinstance(observed, Sequence)
        or isinstance(observed, (str, bytes, bytearray))
    ):
        return 0.0
    reference_set = {canonical_json(item) for item in reference}
    observed_set = {canonical_json(item) for item in observed}
    union = reference_set | observed_set
    if not union:
        return 1.0
    return len(reference_set & observed_set) / len(union)


def _sequence_score(reference: Any, observed: Any) -> float:
    if (
        not isinstance(reference, Sequence)
        or isinstance(reference, (str, bytes, bytearray))
        or not isinstance(observed, Sequence)
        or isinstance(observed, (str, bytes, bytearray))
    ):
        return 0.0
    left = [canonical_json(item) for item in reference]
    right = [canonical_json(item) for item in observed]
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0

    previous = [0] * (len(right) + 1)
    for left_item in left:
        current = [0]
        for index, right_item in enumerate(right, start=1):
            if left_item == right_item:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1] / max(len(left), len(right))


def _compare(feature: TargetFeature, reference: Any, observed: Any) -> float:
    if reference is _MISSING or observed is _MISSING:
        return 0.0
    if feature.comparison == ComparisonMode.EXACT:
        return 1.0 if canonical_json(reference) == canonical_json(observed) else 0.0
    if feature.comparison == ComparisonMode.NUMERIC:
        return _numeric_score(reference, observed, feature.tolerance)
    if feature.comparison == ComparisonMode.SET:
        return _set_score(reference, observed)
    if feature.comparison == ComparisonMode.SEQUENCE:
        return _sequence_score(reference, observed)
    raise ValueError(f"unsupported comparison mode: {feature.comparison}")


def _receipt_core(
    *,
    algorithm_version: str,
    representation_id: str,
    target_id: str,
    input_hash: str,
    gsr: float,
    ngr: float,
    measurements: tuple[FeatureMeasurement, ...],
    provenance: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "algorithm_version": algorithm_version,
        "representation_id": representation_id,
        "target_id": target_id,
        "input_hash": input_hash,
        "gsr": gsr,
        "ngr": ngr,
        "feature_measurements": [measurement.to_record() for measurement in measurements],
        "provenance": list(provenance),
    }


def measure_specificity(representation: Representation) -> MeasurementReceipt:
    """Measure one encoded form against its declared target-relevant record."""

    measurements = []
    input_features = []
    weighted_score = 0.0
    total_weight = 0.0

    for feature in representation.target.features:
        reference = _extract_path(representation.full_record, feature.reference_path)
        observed = _extract_path(representation.geometric_form, feature.encoded_path)
        score = round(_compare(feature, reference, observed), 12)
        measurement = FeatureMeasurement(
            name=feature.name,
            comparison=feature.comparison,
            weight=feature.weight,
            score=score,
            reference_hash=_hash_value(reference),
            observed_hash=_hash_value(observed),
            reference_missing=reference is _MISSING,
            observed_missing=observed is _MISSING,
        )
        measurements.append(measurement)
        weighted_score += score * feature.weight
        total_weight += feature.weight
        input_features.append(
            {
                "target": feature.to_record(),
                "reference_hash": measurement.reference_hash,
                "observed_hash": measurement.observed_hash,
                "reference_missing": measurement.reference_missing,
                "observed_missing": measurement.observed_missing,
            }
        )

    gsr = round(weighted_score / total_weight, 12)
    ngr = round(1.0 - gsr, 12)
    input_record = {
        "algorithm_version": ALGORITHM_VERSION,
        "representation_id": representation.representation_id,
        "target": representation.target.to_record(),
        "features": input_features,
        "provenance": list(representation.provenance),
    }
    input_hash = hashlib.sha256(canonical_json(input_record).encode("utf-8")).hexdigest()
    measurement_tuple = tuple(measurements)
    core = _receipt_core(
        algorithm_version=ALGORITHM_VERSION,
        representation_id=representation.representation_id,
        target_id=representation.target.target_id,
        input_hash=input_hash,
        gsr=gsr,
        ngr=ngr,
        measurements=measurement_tuple,
        provenance=representation.provenance,
    )
    receipt_id = "specificity-" + hashlib.sha256(
        canonical_json(core).encode("utf-8")
    ).hexdigest()
    return MeasurementReceipt(
        receipt_id=receipt_id,
        algorithm_version=ALGORITHM_VERSION,
        representation_id=representation.representation_id,
        target_id=representation.target.target_id,
        input_hash=input_hash,
        gsr=gsr,
        ngr=ngr,
        feature_measurements=measurement_tuple,
        provenance=representation.provenance,
    )


def verify_receipt(receipt: MeasurementReceipt) -> bool:
    """Verify receipt arithmetic and its content-addressed identifier."""

    if not receipt.feature_measurements:
        return False
    total_weight = sum(item.weight for item in receipt.feature_measurements)
    if total_weight <= 0:
        return False
    expected_gsr = round(
        sum(item.score * item.weight for item in receipt.feature_measurements)
        / total_weight,
        12,
    )
    if expected_gsr != receipt.gsr or round(1.0 - receipt.gsr, 12) != receipt.ngr:
        return False
    if any(
        item.score < 0.0 or item.score > 1.0 or item.weight <= 0.0
        for item in receipt.feature_measurements
    ):
        return False
    core = _receipt_core(
        algorithm_version=receipt.algorithm_version,
        representation_id=receipt.representation_id,
        target_id=receipt.target_id,
        input_hash=receipt.input_hash,
        gsr=receipt.gsr,
        ngr=receipt.ngr,
        measurements=receipt.feature_measurements,
        provenance=receipt.provenance,
    )
    expected_id = "specificity-" + hashlib.sha256(
        canonical_json(core).encode("utf-8")
    ).hexdigest()
    return expected_id == receipt.receipt_id
