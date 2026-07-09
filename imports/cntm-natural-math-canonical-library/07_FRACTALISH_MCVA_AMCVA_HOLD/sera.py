from __future__ import annotations


def compute_sera_metrics(
    *,
    total_samples: int,
    hold_count: int,
    committed_correct: int,
    committed_total: int,
    prevented_false_positives: int,
) -> dict[str, float]:
    coverage = committed_total / total_samples if total_samples else 0.0
    hold_rate = hold_count / total_samples if total_samples else 0.0
    valid_committed = committed_correct / committed_total if committed_total else 0.0
    review_load_rate = hold_rate
    return {
        "coverage": round(coverage, 8),
        "hold_rate": round(hold_rate, 8),
        "valid_committed_classification_rate": round(valid_committed, 8),
        "false_positive_commitments_avoided": float(prevented_false_positives),
        "review_load_rate": round(review_load_rate, 8),
    }
