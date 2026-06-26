from __future__ import annotations

from .io import normalize_grayscale


def preprocess_grayscale(grayscale: list[list[int]]) -> tuple[list[list[int]], dict[str, object]]:
    normalized = normalize_grayscale(grayscale)
    metadata = {
        "normalization": "minmax_grayscale",
        "contrast_equalization": False,
        "gaussian_denoise": False,
        "input_min": min(min(row) for row in grayscale) if grayscale and grayscale[0] else 0,
        "input_max": max(max(row) for row in grayscale) if grayscale and grayscale[0] else 0,
    }
    return normalized, metadata
