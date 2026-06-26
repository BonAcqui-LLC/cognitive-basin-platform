from __future__ import annotations

from pathlib import Path

from ._backend import write_comparison_report


def write_case_report(path: Path, record: dict[str, object]) -> None:
    descriptors = record["descriptors"]
    primary = record["primary_family"]
    lines = [
        "# Fractalish Translation Apparatus Report",
        "",
        "## Summary",
        f"- title: {record['title']}",
        f"- routing: {record['routing']}",
        f"- primary family: {primary['family']}",
        f"- primary confidence: {primary['confidence']}",
        f"- dominant geometry: {record['dominant_geometry']}",
        f"- MCVA readability: {record['mcva_readability']}",
        f"- AMCVA primary subtype: {record['amcva_primary_subtype']}",
        "",
        "## Why this family",
    ]
    for reason in primary["reasons"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Minimum descriptors",
            f"- image_width: {descriptors['image_width']}",
            f"- image_height: {descriptors['image_height']}",
            f"- foreground_fraction: {descriptors['foreground_fraction']}",
            f"- connected_component_count: {descriptors['connected_component_count']}",
            f"- contour_count: {descriptors['contour_count']}",
            f"- largest_contour_area: {descriptors['largest_contour_area']}",
            f"- largest_contour_perimeter: {descriptors['largest_contour_perimeter']}",
            f"- perimeter_area_ratio: {descriptors['perimeter_area_ratio']}",
            f"- circularity: {descriptors['circularity']}",
            f"- solidity: {descriptors['solidity']}",
            f"- skeleton_length_px: {descriptors['skeleton_length_px']}",
            f"- endpoint_count: {descriptors['endpoint_count']}",
            f"- junction_count: {descriptors['junction_count']}",
            f"- box_counting_fractal_dimension: {descriptors['box_counting_fractal_dimension']}",
            f"- fractal_dimension_fit_r2: {descriptors['fractal_dimension_fit_r2']}",
            f"- lacunarity_estimate: {descriptors['lacunarity_estimate']}",
            f"- segmentation_quality_score: {descriptors['segmentation_quality_score']}",
            f"- artifact_suspicion_score: {descriptors['artifact_suspicion_score']}",
            "",
            "## Notes",
        ]
    )
    for note in record["notes"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Evidence doctrine",
            "Every claim must travel with its trace.",
            "Similarity is not identity.",
            "Single images classify; sequences explain.",
            "Fractal dimension is one descriptor, not a diagnosis.",
            "This output is not medical, financial, structural, legal, or safety advice.",
            "",
            "## Limitations",
        ]
    )
    for item in record["limitations"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison_markdown(
    path: Path,
    left_record: dict[str, object],
    right_record: dict[str, object],
    comparison: dict[str, object],
) -> None:
    write_comparison_report(path, left_record, right_record, comparison)
