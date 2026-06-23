"""Extension Harness — three-mode unified runner.

Provides a single entry point for local (run_step) and cluster
(run_cluster) operations with three modes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
from typing import Any

sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
import natural_math_v5 as nm

from .registry import ExtensionRegistry
from .context import RunContext
from .local_adapter import run_step_through_harness
from .cluster_adapter import run_cluster_through_harness
from .provenance import create_provenance_record
from .serialization import serialize_run_output


class Mode:
    BASELINE = "BASELINE"
    HARNESS_NO_EXTENSIONS = "HARNESS_NO_EXTENSIONS"
    HARNESS_WITH_EXTENSIONS = "HARNESS_WITH_EXTENSIONS"
    ALL = frozenset({BASELINE, HARNESS_NO_EXTENSIONS, HARNESS_WITH_EXTENSIONS})


def _hash_nodes(nodes):
    s = serialize_run_output(nodes)
    return hashlib.sha256(json.dumps(s, sort_keys=True).encode("utf-8")).hexdigest()


def _make_run_context(mode, seed=None, steps=1):
    run_id = hashlib.sha256(
        f"{seed}_{mode}_{time.time()}".encode()
    ).hexdigest()[:16]
    return RunContext(
        run_id=run_id, mode=mode,
        seed=seed if seed is not None else 0,
        params={}, steps=steps,
        baseline_sha256="e5ab47d41b82f6af573866be637bf3b0054d96c7f45a613ec6cae2124ad84c7b",
        package_manifest_sha256="87b9c28aa27ff5a4e07096da2c62f1ce531e4a89c89c77f29084477f8bae7be9",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def run_local(
    nodes: list[dict[str, Any]],
    params: dict[str, Any],
    mode: str = Mode.BASELINE,
    extensions: list[Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Unified local step runner."""
    if mode not in Mode.ALL:
        raise ValueError(f"Unknown mode: {mode}")

    nodes_copy = copy.deepcopy(nodes)
    params_copy = copy.deepcopy(params)

    if mode == Mode.BASELINE:
        rng_val = kwargs.pop("rng", None)
        bk = {k: kwargs[k] for k in (
            "use_deficit", "use_poc_scream", "allow_bonding",
            "bond_collapse_positions", "bonding_strict",
        ) if k in kwargs}
        if rng_val is not None:
            bk["rng"] = rng_val
        result_nodes = nm.run_step(nodes_copy, params_copy, **bk)
        rh = _hash_nodes(result_nodes)
        prov = create_provenance_record(
            mode=mode, seed=kwargs.get("seed"),
            params=params_copy, steps=1,
            extension_manifests=[], result_hash=rh,
        )
        return {"mode": mode, "result": result_nodes, "provenance": prov,
                "hook_events": [], "extension_manifests": []}

    # Harness modes — extract rng from kwargs before passing
    rng_val = kwargs.pop("rng", None)
    reg = ExtensionRegistry()
    exts = extensions or []
    manifests = []
    if mode == Mode.HARNESS_WITH_EXTENSIONS:
        for ext in exts:
            m = ext.get_manifest()
            reg.register(ext, m)
            manifests.append(m)

    ctx = _make_run_context(mode, seed=kwargs.get("seed"))
    result_nodes, hook_events = run_step_through_harness(
        nodes_copy, params_copy, reg, ctx, rng=rng_val, **kwargs)

    rh = _hash_nodes(result_nodes)
    prov = create_provenance_record(
        mode=mode, seed=kwargs.get("seed"),
        params=params_copy, steps=1,
        extension_manifests=manifests, result_hash=rh,
    )
    return {"mode": mode, "result": result_nodes, "provenance": prov,
            "hook_events": hook_events,
            "extension_manifests": [m.to_dict() for m in manifests]}


def run_cluster(
    seed: int,
    params: dict[str, Any] | None = None,
    steps: int = 140,
    mode: str = Mode.BASELINE,
    extensions: list[Any] | None = None,
) -> dict[str, Any]:
    """Unified cluster runner."""
    if mode not in Mode.ALL:
        raise ValueError(f"Unknown mode: {mode}")

    if mode == Mode.BASELINE:
        result = nm.run_cluster(seed=seed, params=params, steps=steps)
        s = serialize_run_output(result)
        rh = hashlib.sha256(json.dumps(s, sort_keys=True).encode("utf-8")).hexdigest()
        prov = create_provenance_record(
            mode=mode, seed=seed,
            params=params if params else nm.default_params(),
            steps=steps, extension_manifests=[], result_hash=rh,
        )
        return {"mode": mode, "result": result, "provenance": prov,
                "hook_events": [], "extension_manifests": []}

    # Harness modes
    reg = ExtensionRegistry()
    exts = extensions or []
    manifests = []
    if mode == Mode.HARNESS_WITH_EXTENSIONS:
        for ext in exts:
            m = ext.get_manifest()
            reg.register(ext, m)
            manifests.append(m)

    ctx = _make_run_context(mode, seed=seed, steps=steps)
    result, hook_events = run_cluster_through_harness(
        seed=seed, params=params, steps=steps,
        registry=reg, run_context=ctx,
    )
    s = serialize_run_output(result)
    rh = hashlib.sha256(json.dumps(s, sort_keys=True).encode("utf-8")).hexdigest()
    prov = create_provenance_record(
        mode=mode, seed=seed,
        params=params if params else nm.default_params(),
        steps=steps, extension_manifests=manifests, result_hash=rh,
    )
    return {"mode": mode, "result": result, "provenance": prov,
            "hook_events": hook_events,
            "extension_manifests": [m.to_dict() for m in manifests]}
