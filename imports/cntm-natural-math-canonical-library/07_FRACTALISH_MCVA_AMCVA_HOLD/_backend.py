from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCVA_SRC = ROOT / "mcva-public" / "src"
if str(MCVA_SRC) not in sys.path:
    sys.path.insert(0, str(MCVA_SRC))

from mcva.commons import (  # type: ignore
    build_shared_descriptor_rows,
    compute_amcva_scores,
    extract_commons_descriptors,
    flatten_metrics,
    generate_branching_tree_grid,
    generate_hilbert_like_grid,
    generate_noise_grid,
    generate_recovery_wake_grid,
    generate_sierpinski_triangle_grid,
    geometry_signal_profile,
    load_image_grayscale,
    otsu_threshold,
    rank_morphology_families,
    route_case,
    sha256_path,
    sha256_text,
    skeleton_graph_summary,
    write_binary_grid_png,
    write_comparison_report,
    write_overlay_png,
    write_png_rgb,
    write_rows_csv,
    write_rows_xlsx,
    write_side_by_side_trace,
    write_trace_svg,
    zhang_suen_thinning,
    binarize_grayscale,
)
