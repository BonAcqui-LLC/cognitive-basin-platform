from __future__ import annotations

from pathlib import Path

from ._backend import (
    generate_branching_tree_grid,
    generate_hilbert_like_grid,
    generate_noise_grid,
    generate_recovery_wake_grid,
    write_binary_grid_png,
)


def generate_example_images(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    examples = {
        "sample.png": generate_branching_tree_grid(256, depth=6),
        "synthetic_branching.png": generate_branching_tree_grid(256, depth=6),
        "synthetic_irregular_boundary.png": generate_hilbert_like_grid(order=5, size=256),
        "synthetic_polygonal_cells.png": _polygonal_cells_grid(256, 256, spacing=32, thickness=3),
        "synthetic_crack.png": generate_recovery_wake_grid(256, 192),
        "synthetic_noise.png": generate_noise_grid(160, 160),
    }
    written: list[Path] = []
    for name, grid in examples.items():
        target = output_dir / name
        write_binary_grid_png(target, grid)
        written.append(target)
    return written


def _polygonal_cells_grid(width: int, height: int, *, spacing: int, thickness: int) -> list[list[int]]:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(0, height, spacing):
        for col in range(width):
            for offset in range(thickness):
                rr = min(height - 1, row + offset)
                grid[rr][col] = 1
    for col in range(0, width, spacing):
        for row in range(height):
            for offset in range(thickness):
                cc = min(width - 1, col + offset)
                grid[row][cc] = 1
    for band in range(0, height + width, spacing):
        for row in range(height):
            col = band - row
            if 0 <= col < width:
                for offset in range(thickness):
                    cc = min(width - 1, col + offset)
                    grid[row][cc] = 1
    return grid
