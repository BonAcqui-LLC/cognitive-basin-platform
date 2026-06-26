from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ._backend import (
    build_shared_descriptor_rows,
    flatten_metrics,
    sha256_path,
    sha256_text,
    write_binary_grid_png,
    write_rows_csv,
    write_rows_xlsx,
)
from .classify import classify_morphology
from .contours import extract_contour_grid
from .io import combine_rgb_rows, load_grayscale_image, save_grayscale_png, save_rgb_png
from .metrics import extract_metrics
from .preprocess import preprocess_grayscale
from .reports import write_case_report, write_comparison_markdown
from .routing import route_analysis
from .schemas import BATCH_SCHEMA, CASE_SCHEMA, COMPARISON_SCHEMA, REFERENCE_LIBRARY_SCHEMA
from .segmentation import segment_image
from .skeleton import skeletonize_mask
from .svg_export import export_side_by_side_trace, export_trace_svg


REFERENCE_LIBRARY_FAMILIES = [
    "branching_arborizing",
    "crack_fracture",
    "dendritic_growth",
    "vascular_transport",
    "channel_delta",
    "boundary_complexity_irregular_nuclei",
    "polygonal_patterned_ground",
    "porous_lacunary",
    "spiral_vortex",
    "wave_periodic",
    "lattice_grid",
    "filament_web",
    "surface_texture_noise",
    "non_diagnostic_amcva",
]


@dataclass
class CaseArtifacts:
    record: dict[str, object]
    grayscale: list[list[int]]
    normalized: list[list[int]]
    binary_mask: list[list[int]]
    skeleton: list[list[int]]
    contour: list[list[int]]
    overlay_rgb: list[list[tuple[int, int, int]]]


def ensure_reference_library_scaffold(root: Path | None = None) -> Path:
    base = root or Path("data/reference_library")
    base.mkdir(parents=True, exist_ok=True)
    for family in REFERENCE_LIBRARY_FAMILIES:
        (base / family).mkdir(parents=True, exist_ok=True)
    manifest_path = base / "manifest.json"
    if not manifest_path.exists():
        manifest = {
            "schema": REFERENCE_LIBRARY_SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [],
            "note": "Most institutions have not studied fractals as longitudinal process signals. Fractalish stores local-first reference examples, traces, and baseline descriptors here.",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def analyze_image(
    input_path: Path,
    output_dir: Path,
    *,
    title: str | None = None,
    domain: str = "unknown",
    subdomain: str = "unknown",
    source: str = "",
    family_hint: str = "",
) -> dict[str, object]:
    artifacts = _build_case_artifacts(
        input_path,
        title=title,
        domain=domain,
        subdomain=subdomain,
        source=source,
        family_hint=family_hint,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_case_outputs(output_dir, input_path, artifacts)
    return artifacts.record


def compare_images(left_path: Path, right_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    left = _build_case_artifacts(left_path, title=left_path.stem)
    right = _build_case_artifacts(right_path, title=right_path.stem)

    export_trace_svg(
        output_dir / "image_a_trace.svg",
        grayscale=left.normalized,
        skeleton=left.skeleton,
        routing=str(left.record["routing"]),
        primary_family=str(left.record["primary_family_match"]),
        metadata=_svg_metadata(left.record),
    )
    export_trace_svg(
        output_dir / "image_b_trace.svg",
        grayscale=right.normalized,
        skeleton=right.skeleton,
        routing=str(right.record["routing"]),
        primary_family=str(right.record["primary_family_match"]),
        metadata=_svg_metadata(right.record),
    )
    export_side_by_side_trace(
        output_dir / "side_by_side_trace.svg",
        output_dir / "image_a_trace.svg",
        output_dir / "image_b_trace.svg",
        str(left.record["title"]),
        str(right.record["title"]),
    )
    comparison_overlay = combine_rgb_rows(left.overlay_rgb, right.overlay_rgb)
    save_rgb_png(output_dir / "comparison_overlay.png", comparison_overlay)

    shared = build_shared_descriptor_rows(
        left.record["descriptors"],
        right.record["descriptors"],
    )
    comparison = {
        "schema": COMPARISON_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "left_title": left.record["title"],
        "right_title": right.record["title"],
        "left_primary_family_match": left.record["primary_family_match"],
        "right_primary_family_match": right.record["primary_family_match"],
        "shared_descriptors": shared["shared"],
        "divergent_descriptors": shared["divergent"],
        "deltas": shared["deltas"],
        "fractal_dimension_delta": shared["deltas"].get("box_counting_fractal_dimension", 0.0),
        "lacunarity_delta": shared["deltas"].get("lacunarity_estimate", 0.0),
        "branch_count_delta": shared["deltas"].get("branch_count", 0.0),
        "endpoint_junction_delta": {
            "endpoint_count": shared["deltas"].get("endpoint_count", 0.0),
            "junction_count": shared["deltas"].get("junction_count", 0.0),
        },
        "density_delta": shared["deltas"].get("network_density", 0.0),
        "anisotropy_delta": shared["deltas"].get("anisotropy_estimate", 0.0),
        "curvature_delta": shared["deltas"].get("curvature_estimate", 0.0),
        "left_record": "image_a_record.json",
        "right_record": "image_b_record.json",
    }

    rows = [
        {
            "metric": metric,
            "left": left.record["descriptors"].get(metric, ""),
            "right": right.record["descriptors"].get(metric, ""),
            "delta": delta,
        }
        for metric, delta in shared["deltas"].items()
    ]
    write_rows_csv(output_dir / "comparison_metrics.csv", rows)
    write_rows_xlsx(output_dir / "comparison_metrics.xlsx", rows, sheet_name="comparison")
    write_comparison_markdown(output_dir / "comparison_report.md", left.record, right.record, comparison)
    (output_dir / "comparison_record.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (output_dir / "image_a_record.json").write_text(json.dumps(left.record, indent=2), encoding="utf-8")
    (output_dir / "image_b_record.json").write_text(json.dumps(right.record, indent=2), encoding="utf-8")
    return comparison


def batch_analyze_folder(input_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = output_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pgm", ".pbm", ".ppm", ".bmp", ".tif", ".tiff"}
    )
    records: list[dict[str, object]] = []
    for index, path in enumerate(paths, start=1):
        case_dir = cases_dir / f"case_{index:04d}"
        records.append(analyze_image(path, case_dir, title=path.stem))

    rows = [
        {
            "case": f"case_{index:04d}",
            "title": record["title"],
            "routing": record["routing"],
            "primary_family_match": record["primary_family_match"],
            "dominant_geometry": record["dominant_geometry"],
            "confidence": record["confidence"],
            "box_counting_fractal_dimension": record["descriptors"]["box_counting_fractal_dimension"],
        }
        for index, record in enumerate(records, start=1)
    ]
    write_rows_csv(output_dir / "batch_metrics.csv", rows)
    write_rows_xlsx(output_dir / "batch_metrics.xlsx", rows, sheet_name="batch")
    batch_record = {
        "schema": BATCH_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "case_count": len(records),
        "cases": [
            {
                "case": f"case_{index:04d}",
                "title": record["title"],
                "routing": record["routing"],
                "primary_family_match": record["primary_family_match"],
                "record_path": str(cases_dir / f"case_{index:04d}" / "mcva_record.json"),
            }
            for index, record in enumerate(records, start=1)
        ],
    }
    (output_dir / "batch_record.json").write_text(json.dumps(batch_record, indent=2), encoding="utf-8")
    return batch_record


def _build_case_artifacts(
    input_path: Path,
    *,
    title: str | None = None,
    domain: str = "unknown",
    subdomain: str = "unknown",
    source: str = "",
    family_hint: str = "",
) -> CaseArtifacts:
    grayscale, image_meta = load_grayscale_image(input_path)
    normalized, preprocess_meta = preprocess_grayscale(grayscale)
    binary_mask, segmentation_meta = segment_image(normalized)
    skeleton, skeleton_meta = skeletonize_mask(binary_mask)
    contour, _contour_meta = extract_contour_grid(binary_mask)
    raw_sha256 = sha256_path(input_path)
    descriptors = extract_metrics(
        binary_mask=binary_mask,
        skeleton=skeleton,
        grayscale=normalized,
        image_dimensions=(image_meta["width"], image_meta["height"]),
        threshold_method=str(segmentation_meta["threshold_method"]),
        raw_sha256=raw_sha256,
    )
    classified = classify_morphology(
        binary_mask=binary_mask,
        skeleton=skeleton,
        grayscale=normalized,
        descriptors=descriptors,
        family_hint=family_hint,
    )
    routing_meta = route_analysis(
        descriptors,
        classified["geometry_profile"],
        classified["family_matches"],
        classified["amcva_scores"],
    )
    overlay_rgb = _build_overlay_rgb(normalized, contour, skeleton)
    timestamp = datetime.now(timezone.utc).isoformat()
    metrics_hash = sha256_text(json.dumps(descriptors, sort_keys=True))
    primary_family = classified["family_matches"][0] if classified["family_matches"] else {
        "family": "non_diagnostic_amcva",
        "confidence": 0.0,
        "reasons": ["No positive morphology family outran the alternatives."],
    }

    record = {
        "schema": CASE_SCHEMA,
        "title": title or input_path.stem,
        "timestamp": timestamp,
        "input_path": str(input_path),
        "domain": domain,
        "subdomain": subdomain,
        "source": source,
        "routing": routing_meta["routing"],
        "submission_bucket": routing_meta["submission_bucket"],
        "confidence": routing_meta["confidence"],
        "mcva_readability": routing_meta["mcva_readability"],
        "amcva_primary_subtype": routing_meta["amcva_primary_subtype"],
        "amcva_primary_key": routing_meta["amcva_primary_key"],
        "amcva_primary_value": routing_meta["amcva_primary_value"],
        "notes": routing_meta["quality_notes"],
        "preprocess": preprocess_meta,
        "segmentation": segmentation_meta,
        "skeleton": skeleton_meta,
        "primary_family": primary_family,
        "primary_family_match": primary_family["family"],
        "secondary_families": classified["family_matches"][1:4],
        "secondary_family_matches": [item["family"] for item in classified["family_matches"][1:4]],
        "dominant_geometry": classified["geometry_profile"]["dominant_geometry"],
        "secondary_geometry": classified["geometry_profile"]["secondary_geometry"],
        "descriptors": descriptors,
        "geometry_scores": classified["geometry_profile"]["scores"],
        "family_scores": classified["family_matches"],
        "amcva": classified["amcva_scores"],
        "raw_image_hash": raw_sha256,
        "metrics_hash": metrics_hash,
        "guardrails": [
            "Every claim must travel with its trace.",
            "Similarity is not identity.",
            "Single images classify; sequences explain.",
            "Fractal dimension is one descriptor, not a diagnosis.",
            "This output is not medical, financial, structural, legal, or safety advice.",
        ],
        "limitations": [
            "Fractal dimension is not a unique descriptor and is not used alone.",
            "This is a rule-based v0.1 morphology classifier and requires validation.",
            "A single image can suggest a family; it cannot prove the underlying process history.",
            "TODO: multifractal spectrum, recovery-wake scoring, complexity-weighted center, anisotropy export, and time-series support.",
        ],
    }
    return CaseArtifacts(
        record=record,
        grayscale=grayscale,
        normalized=normalized,
        binary_mask=binary_mask,
        skeleton=skeleton,
        contour=contour,
        overlay_rgb=overlay_rgb,
    )


def _write_case_outputs(output_dir: Path, input_path: Path, artifacts: CaseArtifacts) -> None:
    record = artifacts.record
    raw_png = output_dir / "raw_image.png"
    normalized_png = output_dir / "normalized.png"
    mask_png = output_dir / "binary_mask.png"
    skeleton_png = output_dir / "skeleton.png"
    overlay_png = output_dir / "overlay.png"
    trace_svg = output_dir / "morphology_trace.svg"
    metrics_csv = output_dir / "metrics.csv"
    metrics_xlsx = output_dir / "metrics.xlsx"
    record_json = output_dir / "mcva_record.json"
    report_md = output_dir / "report.md"
    save_grayscale_png(raw_png, artifacts.grayscale)
    save_grayscale_png(normalized_png, artifacts.normalized)
    write_binary_grid_png(mask_png, artifacts.binary_mask)
    write_binary_grid_png(skeleton_png, artifacts.skeleton)
    save_rgb_png(overlay_png, artifacts.overlay_rgb)
    export_trace_svg(
        trace_svg,
        grayscale=artifacts.normalized,
        skeleton=artifacts.skeleton,
        routing=str(record["routing"]),
        primary_family=str(record["primary_family_match"]),
        metadata=_svg_metadata(record),
    )
    rows = [{"metric": key, "value": value} for key, value in flatten_metrics(record["descriptors"]).items()]
    write_rows_csv(metrics_csv, rows)
    write_rows_xlsx(metrics_xlsx, rows, sheet_name="metrics")

    record["exports"] = {
        "raw_image_png": str(raw_png),
        "normalized_png": str(normalized_png),
        "binary_mask_png": str(mask_png),
        "skeleton_png": str(skeleton_png),
        "overlay_png": str(overlay_png),
        "morphology_trace_svg": str(trace_svg),
        "metrics_csv": str(metrics_csv),
        "metrics_xlsx": str(metrics_xlsx),
    }
    record["generated_trace_hash"] = sha256_path(trace_svg)
    record_json.write_text(json.dumps(record, indent=2), encoding="utf-8")
    write_case_report(report_md, record)


def _svg_metadata(record: dict[str, object]) -> dict[str, str]:
    return {
        "domain": str(record["domain"]),
        "source": str(record["source"]),
        "timestamp": str(record["timestamp"]),
        "routing": str(record["routing"]),
        "metrics_hash": str(record["metrics_hash"]),
        "raw_image_hash": str(record["raw_image_hash"]),
    }


def _build_overlay_rgb(
    grayscale: list[list[int]],
    contour: list[list[int]],
    skeleton: list[list[int]],
) -> list[list[tuple[int, int, int]]]:
    height = len(grayscale)
    width = len(grayscale[0]) if height else 0
    out: list[list[tuple[int, int, int]]] = []
    for row in range(height):
        current: list[tuple[int, int, int]] = []
        for col in range(width):
            base = grayscale[row][col]
            pixel = (base, base, base)
            if contour[row][col]:
                pixel = (225, 80, 80)
            if skeleton[row][col]:
                pixel = (70, 235, 120)
            current.append(pixel)
        out.append(current)
    return out
