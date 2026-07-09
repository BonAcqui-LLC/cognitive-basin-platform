from __future__ import annotations

from ._backend import binarize_grayscale, otsu_threshold


def segment_image(grayscale: list[list[int]]) -> tuple[list[list[int]], dict[str, object]]:
    threshold_value = otsu_threshold(grayscale)
    binary_mask, polarity = binarize_grayscale(grayscale, threshold_value)
    foreground = _foreground_ratio(binary_mask)
    warnings: list[str] = []
    if foreground < 0.002:
        warnings.append("Mask is extremely sparse after thresholding.")
    if foreground > 0.82:
        warnings.append("Mask is extremely dense after thresholding.")
    return binary_mask, {
        "threshold_method": f"otsu-{polarity}",
        "threshold_value": threshold_value,
        "foreground_ratio": round(foreground, 8),
        "warnings": warnings,
    }


def _foreground_ratio(grid: list[list[int]]) -> float:
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return 0.0
    return sum(sum(row) for row in grid) / float(height * width)
