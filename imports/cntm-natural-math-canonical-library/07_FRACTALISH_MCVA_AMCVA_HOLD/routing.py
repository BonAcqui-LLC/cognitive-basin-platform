from __future__ import annotations


SUBTYPE_MAP = {
    "absence": "AMCVA-A",
    "obscuration": "AMCVA-O",
    "erasure": "AMCVA-E",
    "domain_mismatch": "AMCVA-D",
    "geometric_dominance": "AMCVA-G",
    "competing_geometry": "AMCVA-C",
    "complementary_geometry": "AMCVA-K",
    "capture_artifact": "AMCVA-H",
}


def route_analysis(
    descriptors: dict[str, object],
    geometry_profile: dict[str, object],
    family_matches: list[dict[str, object]],
    amcva_scores: dict[str, float],
) -> dict[str, object]:
    segmentation_quality = float(descriptors.get("segmentation_quality_score", 0.0))
    fit_r2 = float(descriptors.get("fractal_dimension_fit_r2", 0.0))
    artifact_score = float(descriptors.get("artifact_suspicion_score", 0.0))
    foreground_fraction = float(descriptors.get("foreground_fraction", 0.0))
    best = family_matches[0] if family_matches else {"family": "non_diagnostic_amcva", "confidence": 0.0, "reasons": []}
    confidence = float(best.get("confidence", 0.0))
    branching_score = float(geometry_profile["scores"].get("fractal_branching", 0.0))
    mcva_readability = round((segmentation_quality * 0.55) + (confidence * 0.3) + (branching_score * 0.15), 8)
    amcva_primary_key, amcva_primary_value = max(amcva_scores.items(), key=lambda item: item[1])
    notes = list(descriptors.get("confidence_quality_notes", []))

    if foreground_fraction <= 0.001:
        notes.append("Foreground coverage is effectively absent after thresholding.")
    if segmentation_quality < 0.45:
        notes.append("Segmentation quality is too weak for a stable positive claim.")
    if fit_r2 < 0.45:
        notes.append("Fractal-dimension fit quality is weak across scales.")
    if artifact_score >= 0.3:
        notes.append("Artifact suspicion is elevated; the trace may be real but the measurement stack is not yet trustworthy.")

    if (
        foreground_fraction <= 0.001
        or best["family"] == "non_diagnostic_amcva"
        or segmentation_quality < 0.25
        or artifact_score >= 0.78
        or amcva_primary_value >= 0.66
    ):
        notes.append("AMCVA does not mean nothing is there; it often means the trace or the measurement stack is not yet trustworthy.")
        routing = "AMCVA"
        submission_bucket = "proof-negative"
    elif segmentation_quality < 0.58 or fit_r2 < 0.55 or confidence < 0.58 or amcva_primary_value >= 0.4:
        notes.append("Relevant morphology may be present, but evidence remains ambiguous or under-supported.")
        routing = "HOLD"
        submission_bucket = "hold"
    else:
        notes.append("Readable morphology with adequate segmentation quality for a provisional MCVA routing.")
        routing = "MCVA_CANDIDATE"
        submission_bucket = "proof-positive"

    return {
        "routing": routing,
        "submission_bucket": submission_bucket,
        "confidence": round((segmentation_quality * 0.45) + (confidence * 0.55), 8),
        "quality_notes": _dedupe_notes(notes),
        "mcva_readability": mcva_readability,
        "amcva_primary_subtype": SUBTYPE_MAP[amcva_primary_key],
        "amcva_primary_key": amcva_primary_key,
        "amcva_primary_value": round(amcva_primary_value, 8),
    }


def _dedupe_notes(notes: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for note in notes:
        text = note.strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out
