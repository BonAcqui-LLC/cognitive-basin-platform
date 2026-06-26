from __future__ import annotations

from pathlib import Path

from ._backend import load_image_grayscale, write_png_rgb


def load_grayscale_image(path: Path) -> tuple[list[list[int]], dict[str, int]]:
    return load_image_grayscale(path)


def normalize_grayscale(grayscale: list[list[int]]) -> list[list[int]]:
    if not grayscale or not grayscale[0]:
        return grayscale
    minimum = min(min(row) for row in grayscale)
    maximum = max(max(row) for row in grayscale)
    if maximum <= minimum:
        return [[0 for _ in row] for row in grayscale]
    scale = 255.0 / float(maximum - minimum)
    return [
        [int(round((value - minimum) * scale)) for value in row]
        for row in grayscale
    ]


def grayscale_to_rgb_rows(grayscale: list[list[int]]) -> list[list[tuple[int, int, int]]]:
    return [[(value, value, value) for value in row] for row in grayscale]


def save_grayscale_png(path: Path, grayscale: list[list[int]]) -> None:
    write_png_rgb(path, grayscale_to_rgb_rows(grayscale))


def save_rgb_png(path: Path, rgb_rows: list[list[tuple[int, int, int]]]) -> None:
    write_png_rgb(path, rgb_rows)


def combine_rgb_rows(
    left_rows: list[list[tuple[int, int, int]]],
    right_rows: list[list[tuple[int, int, int]]],
    *,
    gap: int = 12,
    background: tuple[int, int, int] = (10, 13, 13),
) -> list[list[tuple[int, int, int]]]:
    left_height = len(left_rows)
    right_height = len(right_rows)
    left_width = len(left_rows[0]) if left_height else 0
    right_width = len(right_rows[0]) if right_height else 0
    height = max(left_height, right_height)
    width = left_width + gap + right_width

    out: list[list[tuple[int, int, int]]] = []
    for row_index in range(height):
        row: list[tuple[int, int, int]] = []
        for col_index in range(width):
            if col_index < left_width and row_index < left_height:
                row.append(left_rows[row_index][col_index])
            elif left_width <= col_index < left_width + gap:
                row.append(background)
            elif col_index >= left_width + gap and row_index < right_height:
                row.append(right_rows[row_index][col_index - left_width - gap])
            else:
                row.append(background)
        out.append(row)
    return out
