from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def _to_counter(data: dict[str, int] | Counter[str]) -> Counter[str]:
    if isinstance(data, Counter):
        return data
    return Counter({str(k): int(v) for k, v in data.items()})


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counter.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def _jaccard_multiset(c1: Counter[str], c2: Counter[str]) -> float:
    keys = set(c1.keys()) | set(c2.keys())
    if not keys:
        return 1.0
    inter = sum(min(c1.get(k, 0), c2.get(k, 0)) for k in keys)
    union = sum(max(c1.get(k, 0), c2.get(k, 0)) for k in keys)
    return (inter / union) if union else 1.0


def _cosine_multiset(c1: Counter[str], c2: Counter[str]) -> float:
    keys = set(c1.keys()) | set(c2.keys())
    if not keys:
        return 1.0
    dot = sum(c1.get(k, 0) * c2.get(k, 0) for k in keys)
    n1 = math.sqrt(sum(v * v for v in c1.values()))
    n2 = math.sqrt(sum(v * v for v in c2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def _linear_regression_slope(points: list[tuple[float, float]]) -> float:
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


def _rescaled_depth_profile(nodes_by_depth: dict[str, int], bins: int = 20) -> list[float]:
    depth_map = {int(k): int(v) for k, v in nodes_by_depth.items()}
    if not depth_map:
        return [0.0] * bins
    max_depth = max(depth_map.keys())
    arr = [float(depth_map.get(d, 0)) for d in range(max_depth + 1)]
    if max_depth == 0:
        out = [arr[0]] + [0.0] * (bins - 1)
    else:
        out = []
        for i in range(bins):
            x = i * (max_depth / (bins - 1))
            lo = int(math.floor(x))
            hi = int(math.ceil(x))
            if lo == hi:
                out.append(arr[lo])
            else:
                w = x - lo
                out.append(arr[lo] * (1 - w) + arr[hi] * w)
    s = sum(out)
    if s <= 0:
        return [0.0] * bins
    return [v / s for v in out]


def _raw_depth_profile(nodes_by_depth: dict[str, int]) -> list[float]:
    depth_map = {int(k): int(v) for k, v in nodes_by_depth.items()}
    if not depth_map:
        return []
    max_depth = max(depth_map.keys())
    out = [float(depth_map.get(d, 0)) for d in range(max_depth + 1)]
    s = sum(out)
    if s <= 0:
        return [0.0 for _ in out]
    return [v / s for v in out]


def _profile_to_counter(profile: list[float]) -> Counter[str]:
    scaled = [int(round(v * 1_000_000)) for v in profile]
    return Counter({str(i): scaled[i] for i in range(len(scaled)) if scaled[i] > 0})


def compute_metrics(bundle: dict[str, Any]) -> dict[str, Any]:
    summary = bundle["summary"]
    graph = bundle["graph"]
    signatures = bundle["signatures"]

    nodes_by_depth = {str(k): int(v) for k, v in summary["nodes_by_depth"].items()}
    outdegree_distribution = {
        str(k): int(v) for k, v in summary["outdegree_distribution"].items()
    }
    shift_distribution = {str(k): int(v) for k, v in summary["shift_distribution"].items()}
    signature_multiset = _to_counter(signatures["signature_multiset"])
    depth_signature_multiset = {
        str(d): _to_counter(c) for d, c in signatures["depth_signature_multiset"].items()
    }

    entropy_by_depth = {
        str(d): _entropy(counter)
        for d, counter in sorted(depth_signature_multiset.items(), key=lambda x: int(x[0]))
    }
    unique_signatures_by_depth = {
        str(d): len(counter) for d, counter in depth_signature_multiset.items()
    }

    depth_points = [
        (int(d), math.log(max(1, c)))
        for d, c in sorted(nodes_by_depth.items(), key=lambda x: int(x[0]))
    ]
    branch_slope = _linear_regression_slope(depth_points)

    cumulative_nodes_by_depth = {}
    run = 0
    for d, c in sorted(nodes_by_depth.items(), key=lambda x: int(x[0])):
        run += int(c)
        cumulative_nodes_by_depth[str(d)] = run

    max_depth = max((int(d) for d in nodes_by_depth.keys()), default=0)
    confluence = summary.get("confluence", {})
    merge_nodes = int(confluence.get("merge_nodes", 0))
    node_count = int(graph["meta"]["node_count"])
    merge_ratio = (merge_nodes / node_count) if node_count else 0.0

    return {
        "root_label": bundle["root_label"],
        "root_value": int(bundle["root_value"]),
        "node_count": node_count,
        "edge_count": int(graph["meta"]["edge_count"]),
        "max_depth": int(max_depth),
        "nodes_by_depth": nodes_by_depth,
        "cumulative_nodes_by_depth": cumulative_nodes_by_depth,
        "outdegree_distribution": outdegree_distribution,
        "shift_distribution": shift_distribution,
        "unique_signatures": len(signature_multiset),
        "unique_signatures_by_depth": unique_signatures_by_depth,
        "signature_multiset": dict(signature_multiset),
        "depth_signature_multiset": {
            d: dict(counter) for d, counter in depth_signature_multiset.items()
        },
        "entropy_by_depth": entropy_by_depth,
        "branch_growth_slope": branch_slope,
        "confluence": {
            "merge_nodes": merge_nodes,
            "merge_ratio": merge_ratio,
            "max_indegree": int(confluence.get("max_indegree", 0)),
            "max_indegree_node": confluence.get("max_indegree_node"),
        },
        "root_signature": signatures["root_signature"],
    }


def compare_automata(
    left: dict[str, Any],
    right: dict[str, Any],
    normalize_depth: bool = True,
) -> dict[str, Any]:
    lm = compute_metrics(left)
    rm = compute_metrics(right)

    left_sig = _to_counter(lm["signature_multiset"])
    right_sig = _to_counter(rm["signature_multiset"])
    left_shift = _to_counter(lm["shift_distribution"])
    right_shift = _to_counter(rm["shift_distribution"])

    sig_jaccard = _jaccard_multiset(left_sig, right_sig)
    sig_cosine = _cosine_multiset(left_sig, right_sig)
    shift_cosine = _cosine_multiset(left_shift, right_shift)
    shift_jaccard = _jaccard_multiset(left_shift, right_shift)

    left_depth = {int(k): _to_counter(v) for k, v in lm["depth_signature_multiset"].items()}
    right_depth = {int(k): _to_counter(v) for k, v in rm["depth_signature_multiset"].items()}
    common_max_depth = min(max(left_depth.keys(), default=0), max(right_depth.keys(), default=0))

    lcp_depth = -1
    first_divergence_depth = None
    for d in range(common_max_depth + 1):
        if left_depth.get(d, Counter()) == right_depth.get(d, Counter()):
            lcp_depth = d
        else:
            first_divergence_depth = d
            break

    if first_divergence_depth is None and (
        max(left_depth.keys(), default=0) != max(right_depth.keys(), default=0)
    ):
        first_divergence_depth = common_max_depth + 1

    if normalize_depth:
        left_profile = _rescaled_depth_profile(lm["nodes_by_depth"])
        right_profile = _rescaled_depth_profile(rm["nodes_by_depth"])
    else:
        left_profile = _raw_depth_profile(lm["nodes_by_depth"])
        right_profile = _raw_depth_profile(rm["nodes_by_depth"])
        if len(left_profile) != len(right_profile):
            max_len = max(len(left_profile), len(right_profile))
            left_profile = left_profile + [0.0] * (max_len - len(left_profile))
            right_profile = right_profile + [0.0] * (max_len - len(right_profile))

    profile_cosine = _cosine_multiset(
        _profile_to_counter(left_profile), _profile_to_counter(right_profile)
    )

    branch_slope_diff = abs(float(lm["branch_growth_slope"]) - float(rm["branch_growth_slope"]))
    merge_ratio_diff = abs(
        float(lm["confluence"]["merge_ratio"]) - float(rm["confluence"]["merge_ratio"])
    )

    left_sig_set = set(left_sig.keys())
    right_sig_set = set(right_sig.keys())
    common_signatures = left_sig_set & right_sig_set
    union_signatures = left_sig_set | right_sig_set
    common_signature_count = len(common_signatures)
    shared_state_ratio_union = (
        common_signature_count / len(union_signatures) if union_signatures else 1.0
    )
    shared_state_ratio_left = (
        common_signature_count / len(left_sig_set) if left_sig_set else 1.0
    )
    shared_state_ratio_right = (
        common_signature_count / len(right_sig_set) if right_sig_set else 1.0
    )

    similarity_score = (
        0.35 * sig_cosine
        + 0.20 * sig_jaccard
        + 0.20 * profile_cosine
        + 0.15 * shift_cosine
        + 0.10 * max(0.0, 1.0 - min(1.0, branch_slope_diff))
    )
    tree_edit_surrogate = 1.0 - similarity_score

    if lm["root_signature"] == rm["root_signature"] and first_divergence_depth is None:
        verdict_en = "identical"
        verdict_ru = "одинаковые"
    elif similarity_score >= 0.78 and merge_ratio_diff < 0.25:
        verdict_en = "similar"
        verdict_ru = "похожие"
    else:
        verdict_en = "different"
        verdict_ru = "разные"

    return {
        "left": lm,
        "right": rm,
        "comparison": {
            "verdict": verdict_ru,
            "verdict_en": verdict_en,
            "normalize_depth": bool(normalize_depth),
            "longest_common_rooted_signature_prefix": lcp_depth,
            "depth_of_first_divergence": first_divergence_depth,
            "signature_jaccard": sig_jaccard,
            "signature_cosine": sig_cosine,
            "shift_jaccard": shift_jaccard,
            "shift_cosine": shift_cosine,
            "rescaled_depth_profile_cosine": profile_cosine,
            "branch_growth_slope_diff": branch_slope_diff,
            "merge_ratio_diff": merge_ratio_diff,
            "common_canonical_signature_count": common_signature_count,
            "shared_canonical_state_ratio_union": shared_state_ratio_union,
            "shared_canonical_state_ratio_left": shared_state_ratio_left,
            "shared_canonical_state_ratio_right": shared_state_ratio_right,
            "approx_tree_edit_distance": tree_edit_surrogate,
            "similarity_score": similarity_score,
        },
        "scale_analogy": {
            "depth_rescaled_branching_match": profile_cosine,
            "shift_frequency_match": shift_cosine,
            "branch_growth_law_match": max(0.0, 1.0 - min(1.0, branch_slope_diff)),
            "canonical_confluence_similarity": max(0.0, 1.0 - min(1.0, merge_ratio_diff)),
        },
    }


def save_comparison(data: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
