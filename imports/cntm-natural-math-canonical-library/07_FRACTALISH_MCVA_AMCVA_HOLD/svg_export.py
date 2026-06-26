from __future__ import annotations

from pathlib import Path

from ._backend import write_side_by_side_trace, write_trace_svg


def export_trace_svg(
    path: Path,
    *,
    grayscale: list[list[int]],
    skeleton: list[list[int]],
    routing: str,
    primary_family: str,
    metadata: dict[str, str],
) -> None:
    write_trace_svg(
        path=path,
        grayscale=grayscale,
        skeleton=skeleton,
        routing=routing,
        primary_family=primary_family,
        metadata=metadata,
    )


def export_side_by_side_trace(
    path: Path,
    left_trace: Path,
    right_trace: Path,
    left_title: str,
    right_title: str,
) -> None:
    write_side_by_side_trace(path, left_trace, right_trace, left_title, right_title)
