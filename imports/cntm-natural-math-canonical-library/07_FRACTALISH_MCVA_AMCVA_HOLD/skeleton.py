from __future__ import annotations

from ._backend import skeleton_graph_summary, zhang_suen_thinning


def skeletonize_mask(binary_mask: list[list[int]]) -> tuple[list[list[int]], dict[str, object]]:
    skeleton = zhang_suen_thinning(binary_mask)
    endpoint_count, junction_count, branch_lengths, branch_angles = skeleton_graph_summary(skeleton)
    metadata = {
        "endpoint_count": endpoint_count,
        "junction_count": junction_count,
        "branch_count": len(branch_lengths),
        "branch_lengths": branch_lengths,
        "branch_angles": branch_angles,
    }
    return skeleton, metadata
