from __future__ import annotations

from ._backend import compute_amcva_scores, geometry_signal_profile


FAMILY_ORDER = [
    "branching_arborizing",
    "crack_fracture",
    "dendritic_growth",
    "vascular_transport",
    "channel_delta",
    "boundary_complexity_irregular_nuclei",
    "polygonal_patterned_ground",
    "porous_lacunary",
    "spiral_vortex",
    "wave_periodic",
    "lattice_grid",
    "filament_web",
    "surface_texture_noise",
    "non_diagnostic_amcva",
]


def classify_morphology(
    *,
    binary_mask: list[list[int]],
    skeleton: list[list[int]],
    grayscale: list[list[int]],
    descriptors: dict[str, object],
    family_hint: str = "",
) -> dict[str, object]:
    geometry_profile = geometry_signal_profile(binary_mask, skeleton, grayscale, _backfill_backend_descriptors(descriptors))
    scores = _family_scores(descriptors, geometry_profile["scores"], family_hint=family_hint)
    family_matches = sorted(scores, key=lambda item: item["confidence"], reverse=True)
    amcva_scores = compute_amcva_scores(_backfill_backend_descriptors(descriptors), geometry_profile, _family_matches_for_amcva(family_matches))
    return {
        "geometry_profile": geometry_profile,
        "family_matches": family_matches,
        "amcva_scores": amcva_scores,
    }


def _family_scores(
    descriptors: dict[str, object],
    geometry_scores: dict[str, float],
    *,
    family_hint: str = "",
) -> list[dict[str, object]]:
    branch_count = float(descriptors.get("branch_count", 0.0))
    junction_count = float(descriptors.get("junction_count", 0.0))
    endpoint_count = float(descriptors.get("endpoint_count", 0.0))
    endpoint_density = float(descriptors.get("endpoint_density", 0.0))
    junction_density = float(descriptors.get("junction_density", 0.0))
    largest_component_fraction = float(descriptors.get("largest_component_fraction", 0.0))
    perimeter_area_ratio = float(descriptors.get("perimeter_area_ratio", 0.0))
    circularity = float(descriptors.get("circularity", 0.0))
    solidity = float(descriptors.get("solidity", 0.0))
    fd = float(descriptors.get("box_counting_fractal_dimension", 0.0))
    lacunarity = float(descriptors.get("lacunarity_estimate", 0.0))
    segmentation_quality = float(descriptors.get("segmentation_quality_score", 0.0))
    artifact_score = float(descriptors.get("artifact_suspicion_score", 0.0))
    foreground_fraction = float(descriptors.get("foreground_fraction", 0.0))
    anisotropy = float(descriptors.get("anisotropy_estimate", 0.0))
    curvature = float(descriptors.get("curvature_estimate", 0.0))
    periodicity = float(descriptors.get("periodicity_score", 0.0))
    radial = float(descriptors.get("radial_symmetry_score", 0.0))
    branch_asymmetry = float(descriptors.get("branch_asymmetry", 0.0))
    dominant_ratio = float(descriptors.get("dominant_recessive_branch_ratio", 0.0))
    contour_count = float(descriptors.get("contour_count", 0.0))
    component_count = float(descriptors.get("connected_component_count", 0.0))

    def note(condition: bool, text: str) -> list[str]:
        return [text] if condition else []

    families: list[dict[str, object]] = []

    branching_score = _clamp01(
        (geometry_scores["fractal_branching"] * 0.45)
        + (_norm(junction_count, 1.0, 24.0) * 0.2)
        + (_norm(branch_count, 2.0, 96.0) * 0.15)
        + (_norm(fd, 1.1, 1.85) * 0.1)
        + (_norm(segmentation_quality, 0.45, 0.95) * 0.1)
    )
    families.append(
        _family(
            "branching_arborizing",
            branching_score,
            note(junction_count >= 2, "Repeated branch junctions detected")
            + note(fd >= 1.18, "Scale complexity exceeds a trivial line")
            + note(endpoint_count >= 4, "Multiple terminal endpoints detected"),
            family_hint,
        )
    )

    crack_score = _clamp01(
        (geometry_scores["crack_network"] * 0.45)
        + (_norm(anisotropy, 0.2, 0.95) * 0.2)
        + (_norm(endpoint_density, 0.01, 0.18) * 0.15)
        + (_norm(perimeter_area_ratio, 0.1, 1.8) * 0.1)
        + (_norm(lacunarity, 1.0, 3.2) * 0.1)
    )
    families.append(
        _family(
            "crack_fracture",
            crack_score,
            note(anisotropy >= 0.35, "Directional fracture bias is elevated")
            + note(endpoint_count >= 3, "Open branch termini support a fracture reading")
            + note(perimeter_area_ratio >= 0.25, "Boundary roughness is high relative to filled area"),
            family_hint,
        )
    )

    dendritic_score = _clamp01(
        (geometry_scores["fractal_branching"] * 0.35)
        + (_norm(branch_asymmetry, 0.05, 0.7) * 0.2)
        + (_norm(dominant_ratio, 1.0, 6.0) * 0.15)
        + (_norm(fd, 1.2, 1.95) * 0.15)
        + (_norm(curvature, 0.2, 2.5) * 0.15)
    )
    families.append(
        _family(
            "dendritic_growth",
            dendritic_score,
            note(branch_count >= 5, "Repeated branch splitting is present")
            + note(dominant_ratio >= 1.3, "Dominant versus recessive branch imbalance is visible")
            + note(curvature >= 0.4, "Growth path curvature is above baseline"),
            family_hint,
        )
    )

    vascular_score = _clamp01(
        (geometry_scores["fractal_branching"] * 0.3)
        + (_norm(largest_component_fraction, 0.55, 1.0) * 0.25)
        + (_norm(solidity, 0.25, 0.95) * 0.15)
        + (_norm(junction_density, 0.002, 0.05) * 0.15)
        + ((1.0 - artifact_score) * 0.15)
    )
    families.append(
        _family(
            "vascular_transport",
            vascular_score,
            note(largest_component_fraction >= 0.6, "Most foreground mass belongs to a connected transport network")
            + note(junction_count >= 2, "Transport-like branching nodes are present")
            + note(solidity >= 0.35, "Filled support remains coherent rather than fully fragmented"),
            family_hint,
        )
    )

    channel_score = _clamp01(
        (geometry_scores["fractal_branching"] * 0.25)
        + (_norm(lacunarity, 1.1, 3.8) * 0.2)
        + (_norm(branch_asymmetry, 0.08, 0.8) * 0.15)
        + (_norm(perimeter_area_ratio, 0.12, 1.5) * 0.15)
        + (_norm(foreground_fraction, 0.02, 0.35) * 0.1)
        + (_norm(endpoint_count, 2.0, 20.0) * 0.15)
    )
    families.append(
        _family(
            "channel_delta",
            channel_score,
            note(branch_asymmetry >= 0.1, "Child branches are uneven, consistent with routing under constraint")
            + note(lacunarity >= 1.2, "Spacing variance suggests channelized void structure")
            + note(endpoint_count >= 3, "Multiple distributary termini are visible"),
            family_hint,
        )
    )

    boundary_score = _clamp01(
        (_norm(circularity, 0.12, 0.85) * 0.2)
        + (_norm(perimeter_area_ratio, 0.12, 2.2) * 0.35)
        + (_norm(solidity, 0.1, 0.9) * 0.2)
        + ((1.0 - _norm(junction_count, 1.0, 18.0)) * 0.15)
        + (_norm(contour_count, 1.0, 10.0) * 0.1)
    )
    families.append(
        _family(
            "boundary_complexity_irregular_nuclei",
            boundary_score,
            note(contour_count >= 1, "Closed contour detected")
            + note(perimeter_area_ratio >= 0.25, "Boundary roughness is above a smooth baseline")
            + note(junction_count <= 4, "Skeleton branching remains weak relative to boundary complexity"),
            family_hint,
        )
    )

    polygonal_score = _clamp01(
        (geometry_scores["cellular_voronoi"] * 0.35)
        + (geometry_scores["grid_lattice"] * 0.2)
        + (_norm(component_count, 3.0, 120.0) * 0.15)
        + (_norm(solidity, 0.25, 0.95) * 0.1)
        + ((1.0 - endpoint_density) * 0.2)
    )
    families.append(
        _family(
            "polygonal_patterned_ground",
            polygonal_score,
            note(component_count >= 4, "Multiple adjacent cells or regions are present")
            + note(periodicity >= 0.15, "Repeated spacing suggests patterned packing")
            + note(endpoint_density <= 0.05, "Topology is cell-like rather than strongly open-ended"),
            family_hint,
        )
    )

    porous_score = _clamp01(
        (_norm(lacunarity, 1.2, 4.0) * 0.35)
        + (_norm(component_count, 3.0, 150.0) * 0.2)
        + (_norm(foreground_fraction, 0.03, 0.55) * 0.1)
        + (_norm(fd, 1.05, 1.85) * 0.15)
        + ((1.0 - largest_component_fraction) * 0.2)
    )
    families.append(
        _family(
            "porous_lacunary",
            porous_score,
            note(lacunarity >= 1.3, "Gap structure is strongly non-uniform")
            + note(component_count >= 3, "Multiple pores or islands are visible")
            + note(largest_component_fraction <= 0.8, "No single component fully dominates the field"),
            family_hint,
        )
    )

    spiral_score = _clamp01(
        (geometry_scores["spiral_vortex"] * 0.6)
        + (_norm(curvature, 0.4, 3.2) * 0.2)
        + (_norm(radial, 0.1, 0.9) * 0.1)
        + ((1.0 - _norm(junction_count, 1.0, 16.0)) * 0.1)
    )
    families.append(
        _family(
            "spiral_vortex",
            spiral_score,
            note(curvature >= 0.8, "Curvature supports a wrapped or turning path")
            + note(radial >= 0.2, "A radial center is plausible")
            + note(junction_count <= 4, "Topology favors a dominant path over heavy branching"),
            family_hint,
        )
    )

    wave_score = _clamp01(
        (geometry_scores["wave_periodicity"] * 0.55)
        + (_norm(periodicity, 0.1, 1.0) * 0.25)
        + (_norm(curvature, 0.2, 2.5) * 0.1)
        + ((1.0 - _norm(junction_count, 1.0, 18.0)) * 0.1)
    )
    families.append(
        _family(
            "wave_periodic",
            wave_score,
            note(periodicity >= 0.2, "Repeated spacing supports a wave-like reading")
            + note(curvature >= 0.2, "Path curvature is above a rigid straight-line baseline")
            + note(junction_count <= 6, "Branching is modest relative to periodic structure"),
            family_hint,
        )
    )

    lattice_score = _clamp01(
        (geometry_scores["grid_lattice"] * 0.6)
        + (_norm(periodicity, 0.15, 1.0) * 0.15)
        + (_norm(solidity, 0.25, 0.95) * 0.1)
        + ((1.0 - _norm(curvature, 0.5, 3.0)) * 0.15)
    )
    families.append(
        _family(
            "lattice_grid",
            lattice_score,
            note(periodicity >= 0.2, "Repeated orientation or spacing suggests a grid/lattice")
            + note(curvature <= 1.0, "Low curvature supports rectilinear or crystalline order")
            + note(solidity >= 0.25, "Support remains structured rather than dust-like"),
            family_hint,
        )
    )

    filament_score = _clamp01(
        (geometry_scores["fractal_branching"] * 0.3)
        + (_norm(endpoint_density, 0.02, 0.2) * 0.25)
        + (_norm(junction_density, 0.002, 0.06) * 0.2)
        + (_norm(skeleton_length := float(descriptors.get("skeleton_length_px", 0.0)), 50.0, 4000.0) * 0.15)
        + ((1.0 - _norm(foreground_fraction, 0.05, 0.6)) * 0.1)
    )
    families.append(
        _family(
            "filament_web",
            filament_score,
            note(endpoint_density >= 0.02, "Thin linework with open termini is present")
            + note(junction_density >= 0.003, "Web-like connectivity exceeds an isolated filament")
            + note(skeleton_length >= 80.0, "Skeleton length supports a trace network rather than a single blob"),
            family_hint,
        )
    )

    noise_score = _clamp01(
        (_norm(artifact_score, 0.15, 1.0) * 0.35)
        + (_norm(component_count, 10.0, 300.0) * 0.2)
        + ((1.0 - segmentation_quality) * 0.2)
        + ((1.0 - largest_component_fraction) * 0.15)
        + ((1.0 - _norm(fd, 1.1, 1.7)) * 0.1)
    )
    families.append(
        _family(
            "surface_texture_noise",
            noise_score,
            note(artifact_score >= 0.2, "Capture or compression artifact suspicion is elevated")
            + note(component_count >= 8, "Fragment count is high for a coherent single morphology")
            + note(segmentation_quality <= 0.6, "Segmentation quality is weak"),
            family_hint,
        )
    )

    non_diagnostic_score = _clamp01(
        ((1.0 - segmentation_quality) * 0.45)
        + (_norm(artifact_score, 0.1, 1.0) * 0.2)
        + ((1.0 - max(branching_score, crack_score, dendritic_score, vascular_score, channel_score, boundary_score, polygonal_score, porous_score, spiral_score, wave_score, lattice_score, filament_score)) * 0.35)
    )
    families.append(
        _family(
            "non_diagnostic_amcva",
            non_diagnostic_score,
            note(segmentation_quality <= 0.45, "Segmentation quality is too weak for a strong positive family claim")
            + note(artifact_score >= 0.25, "Artifacts or obscuration may dominate the reading")
            + note(non_diagnostic_score >= 0.5, "No positive morphology family clearly outruns the alternatives"),
            family_hint,
        )
    )

    return families


def _family(
    name: str,
    score: float,
    reasons: list[str],
    family_hint: str,
) -> dict[str, object]:
    boosted = _clamp01(score + (0.05 if family_hint and family_hint == name else 0.0))
    return {
        "family": name,
        "confidence": round(boosted, 8),
        "reasons": reasons[:3],
    }


def _family_matches_for_amcva(family_matches: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "family": item["family"],
            "score": item["confidence"],
            "checks": len(item.get("reasons", [])),
        }
        for item in family_matches
    ]


def _backfill_backend_descriptors(descriptors: dict[str, object]) -> dict[str, object]:
    copied = dict(descriptors)
    copied.setdefault("fractal_dimension_box_count", float(descriptors.get("box_counting_fractal_dimension", 0.0)))
    copied.setdefault("segmentation_quality", float(descriptors.get("segmentation_quality_score", 0.0)))
    copied.setdefault("artifact_compression_block_score", float(descriptors.get("artifact_suspicion_score", 0.0)))
    copied.setdefault("component_count", float(descriptors.get("connected_component_count", 0.0)))
    return copied


def _norm(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return _clamp01((value - low) / (high - low))


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
