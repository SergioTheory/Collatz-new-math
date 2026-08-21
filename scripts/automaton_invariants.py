from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _entropy_from_counts(counts: dict[int | str, int] | list[int]) -> float:
    if isinstance(counts, list):
        values = [int(v) for v in counts if int(v) > 0]
    else:
        values = [int(v) for v in counts.values() if int(v) > 0]
    total = sum(values)
    if total <= 0:
        return 0.0
    h = 0.0
    for v in values:
        p = v / total
        h -= p * math.log2(p)
    return h


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _linear_slope(points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    n = len(points)
    sx = sum(x for x, _ in points)
    sy = sum(y for _, y in points)
    sxx = sum(x * x for x, _ in points)
    sxy = sum(x * y for x, y in points)
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0
    return (n * sxy - sx * sy) / den


def _cosine(a: list[float], b: list[float]) -> float:
    n = max(len(a), len(b))
    if n == 0:
        return 1.0
    aa = a + [0.0] * (n - len(a))
    bb = b + [0.0] * (n - len(b))
    dot = sum(x * y for x, y in zip(aa, bb))
    na = math.sqrt(sum(x * x for x in aa))
    nb = math.sqrt(sum(y * y for y in bb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _to_int_depth_map(values: dict[str, int]) -> dict[int, int]:
    return {int(k): int(v) for k, v in values.items()}


def _to_int_map(values: dict[str, int]) -> dict[int, int]:
    return {int(k): int(v) for k, v in values.items()}


def _build_outdegree_by_depth(bundle: dict[str, Any]) -> dict[int, dict[int, int]]:
    graph = bundle["graph"]
    by_depth: dict[int, dict[int, int]] = {}
    for node in graph["nodes"].values():
        d = int(node["min_depth"])
        outd = len(node.get("children", []))
        by_depth.setdefault(d, {})
        by_depth[d][outd] = by_depth[d].get(outd, 0) + 1
    return by_depth


def _build_node_transition_entropies(bundle: dict[str, Any]) -> list[float]:
    graph = bundle["graph"]
    edges_by_source: dict[str, dict[str, int]] = {}

    node_sigs: dict[str, str] = bundle["signatures"]["node_signatures"]
    for edge in graph["edges"]:
        src = str(edge["source"])
        tgt = str(edge["target"])
        label = f"{int(edge['a'])}|{node_sigs.get(tgt, 'NA')}|{str(edge.get('kind', ''))}"
        edges_by_source.setdefault(src, {})
        edges_by_source[src][label] = edges_by_source[src].get(label, 0) + 1

    out = []
    for node_id in graph["nodes"].keys():
        dist = edges_by_source.get(str(node_id), {})
        if not dist:
            out.append(0.0)
            continue
        out.append(_entropy_from_counts(dist))
    return out


def _normalize_hist(values: dict[int, int]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0:
        return {}
    return {str(k): (v / total) for k, v in sorted(values.items(), key=lambda x: x[0])}


def _skewness_from_probabilities(hist: dict[int, int]) -> float:
    total = sum(hist.values())
    if total <= 0:
        return 0.0
    mean = sum(k * v for k, v in hist.items()) / total
    var = sum(((k - mean) ** 2) * v for k, v in hist.items()) / total
    if var <= 0:
        return 0.0
    std = math.sqrt(var)
    m3 = sum(((k - mean) ** 3) * v for k, v in hist.items()) / total
    return m3 / (std ** 3)


def compute_automaton_invariants(bundle: dict[str, Any]) -> dict[str, Any]:
    summary = bundle["summary"]
    signatures = bundle["signatures"]
    graph_meta = bundle["graph"]["meta"]

    nodes_by_depth = _to_int_depth_map(summary["nodes_by_depth"])
    total_nodes = int(graph_meta["node_count"])
    max_depth = int(graph_meta["max_depth"])

    sorted_depths = sorted(nodes_by_depth.keys())
    growth_by_depth: dict[str, float] = {}
    growth_values: list[float] = []
    for d in sorted_depths:
        nd = nodes_by_depth.get(d, 0)
        nnext = nodes_by_depth.get(d + 1, 0)
        if nd > 0 and nnext > 0:
            ratio = nnext / nd
            growth_by_depth[str(d)] = ratio
            growth_values.append(ratio)

    outdegree_by_depth = _build_outdegree_by_depth(bundle)
    entropy_by_depth: dict[str, float] = {}
    for d in sorted(outdegree_by_depth.keys()):
        entropy_by_depth[str(d)] = _entropy_from_counts(outdegree_by_depth[d])
    entropy_values = [entropy_by_depth[k] for k in sorted(entropy_by_depth.keys(), key=int)]
    entropy_gradient: dict[str, float] = {}
    for d in sorted(entropy_by_depth.keys(), key=int):
        di = int(d)
        if str(di + 1) in entropy_by_depth:
            entropy_gradient[d] = entropy_by_depth[str(di + 1)] - entropy_by_depth[d]

    signature_multiset = {str(k): int(v) for k, v in signatures["signature_multiset"].items()}
    signature_entropy = _entropy_from_counts(signature_multiset)

    depth_sig_multiset = signatures["depth_signature_multiset"]
    signature_entropy_by_depth: dict[str, float] = {}
    for d, counter in depth_sig_multiset.items():
        signature_entropy_by_depth[str(d)] = _entropy_from_counts(
            {str(k): int(v) for k, v in counter.items()}
        )

    shift_hist = _to_int_map(summary["shift_distribution"])
    shift_prob = _normalize_hist(shift_hist)
    shift_entropy = _entropy_from_counts(shift_hist)
    shift_skewness = _skewness_from_probabilities(shift_hist)

    outdegree_dist = _to_int_map(summary["outdegree_distribution"])
    deg_total = sum(outdegree_dist.values())
    mean_degree = (
        sum(k * v for k, v in outdegree_dist.items()) / deg_total if deg_total > 0 else 0.0
    )
    var_degree = (
        sum(((k - mean_degree) ** 2) * v for k, v in outdegree_dist.items()) / deg_total
        if deg_total > 0
        else 0.0
    )
    max_degree = max(outdegree_dist.keys(), default=0)
    sparsity = (outdegree_dist.get(0, 0) / deg_total) if deg_total > 0 else 0.0

    width_profile = {str(d): int(nodes_by_depth[d]) for d in sorted_depths}
    max_width = max(nodes_by_depth.values(), default=0)
    depth_of_max_width = None
    if max_width > 0:
        depth_of_max_width = min(d for d, v in nodes_by_depth.items() if v == max_width)
    width_points = []
    for d in sorted_depths:
        norm_depth = (d / max_depth) if max_depth > 0 else 0.0
        norm_width = (nodes_by_depth[d] / total_nodes) if total_nodes > 0 else 0.0
        width_points.append((norm_depth, norm_width))
    width_growth_slope = _linear_slope(width_points)

    depth_sig_sets = {
        int(d): set(str(sig) for sig in counter.keys()) for d, counter in depth_sig_multiset.items()
    }
    overlap_by_depth: dict[str, float] = {}
    overlap_vals: list[float] = []
    for d in sorted(depth_sig_sets.keys()):
        s1 = depth_sig_sets.get(d, set())
        s2 = depth_sig_sets.get(d + 1, set())
        if not s1 and not s2:
            continue
        union = s1 | s2
        inter = s1 & s2
        ov = (len(inter) / len(union)) if union else 1.0
        overlap_by_depth[str(d)] = ov
        overlap_vals.append(ov)

    node_transition_entropy = _build_node_transition_entropies(bundle)
    mean_transition_entropy = _mean(node_transition_entropy)
    var_transition_entropy = _variance(node_transition_entropy)
    max_possible = math.log2(max_degree) if max_degree > 1 else 1.0
    mean_transition_entropy_normalized = (
        mean_transition_entropy / max_possible if max_possible > 0 else 0.0
    )

    return {
        "root": bundle["root_label"],
        "depth": max_depth,
        "growth": {
            "growth_ratio_by_depth": growth_by_depth,
            "list": growth_values,
            "mean": _mean(growth_values),
            "variance": _variance(growth_values),
        },
        "entropy": {
            "branching_entropy_by_depth": entropy_by_depth,
            "mean_entropy": _mean(entropy_values),
            "entropy_gradient": entropy_gradient,
        },
        "signatures": {
            "signature_entropy": signature_entropy,
            "signature_entropy_by_depth": signature_entropy_by_depth,
        },
        "shift": {
            "normalized_histogram": shift_prob,
            "entropy": shift_entropy,
            "skewness": shift_skewness,
        },
        "degree": {
            "mean_degree": mean_degree,
            "variance_degree": var_degree,
            "max_degree": max_degree,
            "sparsity_zero_degree": sparsity,
        },
        "width": {
            "width_profile": width_profile,
            "max_width": max_width,
            "depth_of_max_width": depth_of_max_width,
            "width_growth_slope": width_growth_slope,
        },
        "stability": {
            "overlap_by_depth": overlap_by_depth,
            "mean_overlap": _mean(overlap_vals),
        },
        "transition": {
            "mean_transition_entropy": mean_transition_entropy,
            "variance_transition_entropy": var_transition_entropy,
            "mean_transition_entropy_normalized": mean_transition_entropy_normalized,
        },
    }


def save_invariants(invariants: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(invariants, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def compare_invariants(inv1: dict[str, Any], inv2: dict[str, Any]) -> dict[str, Any]:
    v1 = [
        float(inv1["growth"]["mean"]),
        float(inv1["growth"]["variance"]),
        float(inv1["entropy"]["mean_entropy"]),
        float(inv1["signatures"]["signature_entropy"]),
        float(inv1["shift"]["entropy"]),
        float(inv1["degree"]["mean_degree"]),
        float(inv1["degree"]["variance_degree"]),
        float(inv1["degree"]["sparsity_zero_degree"]),
        float(inv1["width"]["width_growth_slope"]),
        float(inv1["stability"]["mean_overlap"]),
        float(inv1["transition"]["mean_transition_entropy_normalized"]),
    ]
    v2 = [
        float(inv2["growth"]["mean"]),
        float(inv2["growth"]["variance"]),
        float(inv2["entropy"]["mean_entropy"]),
        float(inv2["signatures"]["signature_entropy"]),
        float(inv2["shift"]["entropy"]),
        float(inv2["degree"]["mean_degree"]),
        float(inv2["degree"]["variance_degree"]),
        float(inv2["degree"]["sparsity_zero_degree"]),
        float(inv2["width"]["width_growth_slope"]),
        float(inv2["stability"]["mean_overlap"]),
        float(inv2["transition"]["mean_transition_entropy_normalized"]),
    ]

    l2 = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    core_similarity = 1.0 / (1.0 + l2)

    shift_hist_1 = [float(v) for _, v in sorted(inv1["shift"]["normalized_histogram"].items(), key=lambda x: int(x[0]))]
    shift_hist_2 = [float(v) for _, v in sorted(inv2["shift"]["normalized_histogram"].items(), key=lambda x: int(x[0]))]
    shift_similarity = _cosine(shift_hist_1, shift_hist_2)

    width_1 = [float(v) for _, v in sorted(inv1["width"]["width_profile"].items(), key=lambda x: int(x[0]))]
    width_2 = [float(v) for _, v in sorted(inv2["width"]["width_profile"].items(), key=lambda x: int(x[0]))]
    width_similarity = _cosine(width_1, width_2)

    growth_1 = [float(v) for _, v in sorted(inv1["growth"]["growth_ratio_by_depth"].items(), key=lambda x: int(x[0]))]
    growth_2 = [float(v) for _, v in sorted(inv2["growth"]["growth_ratio_by_depth"].items(), key=lambda x: int(x[0]))]
    growth_similarity = _cosine(growth_1, growth_2)

    entropy_diff = abs(float(inv1["entropy"]["mean_entropy"]) - float(inv2["entropy"]["mean_entropy"]))
    entropy_similarity = 1.0 / (1.0 + entropy_diff)

    similarity_score = (
        0.35 * core_similarity
        + 0.20 * shift_similarity
        + 0.20 * width_similarity
        + 0.15 * growth_similarity
        + 0.10 * entropy_similarity
    )

    return {
        "l2_distance": l2,
        "core_similarity": core_similarity,
        "shift_similarity": shift_similarity,
        "width_similarity": width_similarity,
        "growth_similarity": growth_similarity,
        "entropy_similarity": entropy_similarity,
        "similarity_score": similarity_score,
    }

