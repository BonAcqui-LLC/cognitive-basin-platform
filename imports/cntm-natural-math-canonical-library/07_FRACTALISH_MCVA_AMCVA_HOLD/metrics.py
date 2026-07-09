from __future__ import annotations

import math

import numpy as np
from skimage import measure

from ._backend import extract_commons_descriptors, flatten_metrics


def extract_metrics(
    *,
    binary_mask: list[list[int]],
    skeleton: list[list[int]],
    grayscale: list[list[int]],
    image_dimensions: tuple[int, int],
    threshold_method: str,
    raw_sha256: str,
) -> dict[str, object]:
    arr = np.array(binary_mask, dtype=np.uint8)
    skeleton_arr = np.array(skeleton, dtype=np.uint8)

    base = extract_commons_descriptors(
        binary_mask=binary_mask,
        skeleton=skeleton,
        threshold_method=threshold_method,
        image_dimensions=image_dimensions,
        grayscale=grayscale,
    )

    labels = measure.label(arr, connectivity=2)
    regions = sorted(measure.regionprops(labels), key=lambda region: float(region.area), reverse=True)
    contours = measure.find_contours(arr.astype(float), 0.5)

    foreground_pixels = float(arr.sum())
    total_pixels = float(arr.size) if arr.size else 0.0
    largest_region = regions[0] if regions else None
    largest_area = float(largest_region.area) if largest_region is not None else 0.0
    largest_perimeter = max((_contour_length(contour) for contour in contours), default=0.0)
    largest_component_fraction = (largest_area / foreground_pixels) if foreground_pixels else 0.0
    perimeter_area_ratio = (largest_perimeter / largest_area) if largest_area else 0.0
    circularity = _safe_circularity(largest_area, largest_perimeter)
    solidity = float(getattr(largest_region, "solidity", 0.0) or 0.0) if largest_region is not None else 0.0

    skeleton_length_px = float(skeleton_arr.sum())
    endpoint_count = float(base.get("endpoint_count", 0.0))
    junction_count = float(base.get("junction_count", 0.0))
    junction_density = (junction_count / skeleton_length_px) if skeleton_length_px else 0.0
    endpoint_density = (endpoint_count / skeleton_length_px) if skeleton_length_px else 0.0

    segmentation_quality = float(base.get("segmentation_quality", 0.0))
    artifact_score = float(base.get("artifact_compression_block_score", 0.0))
    segmentation_penalty = max(0.0, 1.0 - segmentation_quality)
    artifact_suspicion = max(artifact_score, round((artifact_score * 0.55) + (segmentation_penalty * 0.45), 8))

    descriptors = {
        "image_width": int(image_dimensions[0]),
        "image_height": int(image_dimensions[1]),
        "raw_sha256": raw_sha256,
        "threshold_method": threshold_method,
        "foreground_fraction": round((foreground_pixels / total_pixels) if total_pixels else 0.0, 8),
        "connected_component_count": int(labels.max()) if labels.size else 0,
        "largest_component_fraction": round(largest_component_fraction, 8),
        "contour_count": len(contours),
        "largest_contour_area": round(largest_area, 8),
        "largest_contour_perimeter": round(largest_perimeter, 8),
        "perimeter_area_ratio": round(perimeter_area_ratio, 8),
        "circularity": round(circularity, 8),
        "solidity": round(solidity, 8),
        "skeleton_length_px": round(skeleton_length_px, 8),
        "endpoint_count": round(endpoint_count, 8),
        "junction_count": round(junction_count, 8),
        "junction_density": round(junction_density, 8),
        "endpoint_density": round(endpoint_density, 8),
        "box_counting_fractal_dimension": round(float(base.get("fractal_dimension_box_count", 0.0)), 8),
        "fractal_dimension_fit_r2": round(float(base.get("fractal_dimension_fit_r2", 0.0)), 8),
        "box_sizes_used": base.get("box_sizes_used", []),
        "occupied_box_counts": base.get("occupied_box_counts", []),
        "scale_range_warning": base.get("scale_range_warning"),
        "lacunarity_estimate": round(float(base.get("lacunarity_estimate", 0.0)), 8),
        "segmentation_quality_score": round(segmentation_quality, 8),
        "artifact_suspicion_score": round(artifact_suspicion, 8),
        "family_todo": [
            "TODO: add multifractal spectrum",
            "TODO: add recovery-wake scoring",
            "TODO: add complexity-weighted center",
            "TODO: add anisotropy-specific export",
            "TODO: add time-series support",
        ],
        "branch_count": round(float(base.get("branch_count", 0.0)), 8),
        "branch_asymmetry": round(float(base.get("branch_asymmetry", 0.0)), 8),
        "dominant_recessive_branch_ratio": round(float(base.get("dominant_recessive_branch_ratio", 0.0)), 8),
        "network_density": round(float(base.get("network_density", 0.0)), 8),
        "anisotropy_estimate": round(float(base.get("anisotropy_estimate", 0.0)), 8),
        "curvature_estimate": round(float(base.get("curvature_estimate", 0.0)), 8),
        "radial_symmetry_score": round(float(base.get("radial_symmetry_score", 0.0)), 8),
        "bilateral_symmetry_score": round(float(base.get("bilateral_symmetry_score", 0.0)), 8),
        "periodicity_score": round(float(base.get("periodicity_score", 0.0)), 8),
        "lattice_grid_orientation": base.get("lattice_grid_orientation", 0.0),
        "dominant_orientation_histogram": base.get("dominant_orientation_histogram", []),
        "confidence_quality_notes": list(base.get("confidence_quality_notes", [])),
    }
    return descriptors


def flatten_metric_values(descriptors: dict[str, object]) -> dict[str, str]:
    return flatten_metrics(descriptors)


def _contour_length(contour: np.ndarray) -> float:
    if len(contour) < 2:
        return 0.0
    diffs = np.diff(contour, axis=0)
    segment_lengths = np.sqrt((diffs ** 2).sum(axis=1))
    return float(segment_lengths.sum())


def _safe_circularity(area: float, perimeter: float) -> float:
    if area <= 0.0 or perimeter <= 0.0:
        return 0.0
    return min(1.0, max(0.0, (4.0 * math.pi * area) / (perimeter * perimeter)))
