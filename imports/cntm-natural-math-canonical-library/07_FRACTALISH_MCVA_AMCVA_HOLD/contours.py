from __future__ import annotations

from collections import deque


def extract_contour_grid(binary_mask: list[list[int]]) -> tuple[list[list[int]], dict[str, object]]:
    height = len(binary_mask)
    width = len(binary_mask[0]) if height else 0
    contour = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            if not binary_mask[row][col]:
                continue
            if any(not _mask_value(binary_mask, row + dr, col + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                contour[row][col] = 1

    contour_pixels = sum(sum(row) for row in contour)
    contour_components = _count_components(contour)
    return contour, {
        "contour_pixels": contour_pixels,
        "contour_component_count": contour_components,
    }


def _mask_value(grid: list[list[int]], row: int, col: int) -> int:
    if row < 0 or col < 0:
        return 0
    if row >= len(grid) or col >= len(grid[0]):
        return 0
    return grid[row][col]


def _count_components(grid: list[list[int]]) -> int:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    count = 0

    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            count += 1
            queue: deque[tuple[int, int]] = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr = current_row + dr
                        nc = current_col + dc
                        if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            queue.append((nr, nc))
    return count
