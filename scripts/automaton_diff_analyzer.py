from __future__ import annotations

import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from automaton_compare import compare_automata, compute_metrics


def _depth_signature_sets(bundle: dict[str, Any]) -> dict[int, set[str]]:
    depth_ms = bundle["signatures"]["depth_signature_multiset"]
    out: dict[int, set[str]] = {}
    for depth, counter in depth_ms.items():
        out[int(depth)] = set(str(k) for k in counter.keys())
    return out


def _edge_maps(graph: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, set[str]]]:
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    neighbors: dict[str, set[str]] = defaultdict(set)
    for edge in graph["edges"]:
        s = str(edge["source"])
        t = str(edge["target"])
        outgoing[s].append(edge)
        neighbors[s].add(t)
        neighbors[t].add(s)
    for node_id in graph["nodes"]:
        outgoing.setdefault(node_id, [])
        neighbors.setdefault(node_id, set())
    return outgoing, neighbors


def _entropy(counter: Counter[int]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counter.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = max(len(a), len(b))
    aa = a + [0.0] * (n - len(a))
    bb = b + [0.0] * (n - len(b))
    dot = sum(x * y for x, y in zip(aa, bb))
    na = math.sqrt(sum(x * x for x in aa))
    nb = math.sqrt(sum(y * y for y in bb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _truncate_sorted(values: set[str] | list[str], max_items: int = 200) -> list[str]:
    if isinstance(values, set):
        seq = sorted(values)
    else:
        seq = sorted(values)
    return seq[:max_items]


def find_first_divergence(
    automaton_a: dict[str, Any],
    automaton_b: dict[str, Any],
    max_items: int = 200,
) -> dict[str, Any]:
    sig_a = _depth_signature_sets(automaton_a)
    sig_b = _depth_signature_sets(automaton_b)
    max_depth = min(max(sig_a.keys(), default=0), max(sig_b.keys(), default=0))

    for depth in range(max_depth + 1):
        set_a = sig_a.get(depth, set())
        set_b = sig_b.get(depth, set())
        if set_a != set_b:
            common = set_a & set_b
            only_a = set_a - set_b
            only_b = set_b - set_a
            return {
                "depth": depth,
                "common_signatures_count": len(common),
                "only_in_A_count": len(only_a),
                "only_in_B_count": len(only_b),
                "common_signatures": _truncate_sorted(common, max_items=max_items),
                "only_in_A": _truncate_sorted(only_a, max_items=max_items),
                "only_in_B": _truncate_sorted(only_b, max_items=max_items),
            }

    # No divergence up to overlap depth
    return {
        "depth": None,
        "common_signatures_count": len(sig_a.get(max_depth, set()) & sig_b.get(max_depth, set())),
        "only_in_A_count": 0,
        "only_in_B_count": 0,
        "common_signatures": _truncate_sorted(
            sig_a.get(max_depth, set()) & sig_b.get(max_depth, set()),
            max_items=max_items,
        ),
        "only_in_A": [],
        "only_in_B": [],
    }


def extract_local_motif(
    automaton: dict[str, Any],
    signature: str,
    depth: int | None,
    radius: int = 2,
) -> dict[str, Any]:
    graph = automaton["graph"]
    nodes = graph["nodes"]
    node_sigs: dict[str, str] = automaton["signatures"]["node_signatures"]
    outgoing, neighbors = _edge_maps(graph)

    candidates = [
        node_id
        for node_id, sig in node_sigs.items()
        if sig == signature and (depth is None or int(nodes[node_id]["min_depth"]) == int(depth))
    ]
    if not candidates:
        candidates = [node_id for node_id, sig in node_sigs.items() if sig == signature]
    if not candidates:
        return {
            "signature": signature,
            "depth": depth,
            "found": False,
        }

    center = min(candidates, key=lambda nid: int(nodes[nid]["value"]))
    center_node = nodes[center]

    q = deque([(center, 0)])
    seen = {center}
    dist_sig: dict[int, Counter[str]] = defaultdict(Counter)
    local_nodes = {center}
    while q:
        cur, d = q.popleft()
        sig = node_sigs.get(cur, "NA")
        dist_sig[d][sig] += 1
        if d >= radius:
            continue
        for nb in neighbors.get(cur, set()):
            if nb not in seen:
                seen.add(nb)
                local_nodes.add(nb)
                q.append((nb, d + 1))

    out_edges = outgoing.get(center, [])
    shift_hist = Counter(int(edge["a"]) for edge in out_edges)
    child_sigs = [node_sigs.get(str(edge["target"]), "NA") for edge in out_edges]
    child_sig_dist = Counter(child_sigs)
    shift_sequence = [int(edge["a"]) for edge in sorted(out_edges, key=lambda e: int(e["a"]))]

    local_edge_count = 0
    local_node_set = set(local_nodes)
    for edge in graph["edges"]:
        if str(edge["source"]) in local_node_set and str(edge["target"]) in local_node_set:
            local_edge_count += 1

    return {
        "signature": signature,
        "depth": int(center_node["min_depth"]),
        "found": True,
        "center_node_id": center,
        "center_value": int(center_node["value"]),
        "degree": len(center_node.get("parents", [])) + len(center_node.get("children", [])),
        "outdegree": len(out_edges),
        "shift_sequence": shift_sequence,
        "shift_hist": {str(k): int(v) for k, v in sorted(shift_hist.items())},
        "children_signatures": sorted(child_sig_dist.keys()),
        "children_signature_distribution": {
            k: int(v) for k, v in sorted(child_sig_dist.items(), key=lambda x: x[0])
        },
        "radius": radius,
        "local_node_count": len(local_nodes),
        "local_edge_count": local_edge_count,
        "signature_shells": {
            str(d): {k: int(v) for k, v in sorted(counter.items(), key=lambda x: x[0])}
            for d, counter in sorted(dist_sig.items(), key=lambda x: x[0])
        },
    }


def _build_transition_counter(automaton: dict[str, Any]) -> Counter[str]:
    graph = automaton["graph"]
    node_sigs: dict[str, str] = automaton["signatures"]["node_signatures"]
    counter: Counter[str] = Counter()
    for edge in graph["edges"]:
        src = str(edge["source"])
        tgt = str(edge["target"])
        key = json.dumps(
            [
                node_sigs.get(src, "NA"),
                int(edge["a"]),
                node_sigs.get(tgt, "NA"),
                str(edge.get("kind", "")),
            ],
            separators=(",", ":"),
        )
        counter[key] += 1
    return counter


def compare_signature_transitions(
    automaton_a: dict[str, Any],
    automaton_b: dict[str, Any],
    max_items: int = 300,
) -> dict[str, Any]:
    ta = _build_transition_counter(automaton_a)
    tb = _build_transition_counter(automaton_b)
    set_a = set(ta.keys())
    set_b = set(tb.keys())
    shared = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a
    union = set_a | set_b
    overlap = (len(shared) / len(union)) if union else 1.0

    return {
        "transition_overlap_ratio": overlap,
        "shared_transitions_count": len(shared),
        "unique_transitions_A_count": len(only_a),
        "unique_transitions_B_count": len(only_b),
        "shared_transitions": _truncate_sorted(shared, max_items=max_items),
        "unique_transitions_A": _truncate_sorted(only_a, max_items=max_items),
        "unique_transitions_B": _truncate_sorted(only_b, max_items=max_items),
    }


def _build_grammar_rules(automaton: dict[str, Any]) -> dict[str, str]:
    graph = automaton["graph"]
    nodes = graph["nodes"]
    node_sigs: dict[str, str] = automaton["signatures"]["node_signatures"]
    outgoing, _ = _edge_maps(graph)

    sig_to_nodes: dict[str, list[str]] = defaultdict(list)
    for node_id, sig in node_sigs.items():
        sig_to_nodes[sig].append(node_id)

    rules: dict[str, str] = {}
    for sig, node_ids in sig_to_nodes.items():
        rep = min(node_ids, key=lambda nid: int(nodes[nid]["value"]))
        produced = []
        for edge in outgoing.get(rep, []):
            child_sig = node_sigs.get(str(edge["target"]), "NA")
            produced.append([int(edge["a"]), child_sig, str(edge.get("kind", ""))])
        produced.sort(key=lambda x: (x[0], x[1], x[2]))
        rules[sig] = json.dumps(produced, separators=(",", ":"))
    return rules


def compare_grammar_rules(
    automaton_a: dict[str, Any],
    automaton_b: dict[str, Any],
    max_items: int = 300,
) -> dict[str, Any]:
    rules_a = _build_grammar_rules(automaton_a)
    rules_b = _build_grammar_rules(automaton_b)

    items_a = {json.dumps([sig, rule], separators=(",", ":")) for sig, rule in rules_a.items()}
    items_b = {json.dumps([sig, rule], separators=(",", ":")) for sig, rule in rules_b.items()}
    shared = items_a & items_b
    only_a = items_a - items_b
    only_b = items_b - items_a
    union = items_a | items_b
    overlap = (len(shared) / len(union)) if union else 1.0

    return {
        "rule_overlap_ratio": overlap,
        "shared_rules_count": len(shared),
        "rules_only_in_A_count": len(only_a),
        "rules_only_in_B_count": len(only_b),
        "rules_only_in_A": _truncate_sorted(only_a, max_items=max_items),
        "rules_only_in_B": _truncate_sorted(only_b, max_items=max_items),
    }


def _shape_metrics(bundle: dict[str, Any]) -> dict[str, Any]:
    graph = bundle["graph"]
    nodes = graph["nodes"]
    metrics = compute_metrics(bundle)
    nodes_by_depth = {int(k): int(v) for k, v in metrics["nodes_by_depth"].items()}
    unique_by_depth = {
        int(k): int(v) for k, v in metrics["unique_signatures_by_depth"].items()
    }

    growth_rate = {}
    depths = sorted(nodes_by_depth.keys())
    for d in depths:
        nxt = d + 1
        if d in nodes_by_depth and nxt in nodes_by_depth and nodes_by_depth[d] > 0 and nodes_by_depth[nxt] > 0:
            growth_rate[str(d)] = math.log(nodes_by_depth[nxt] / nodes_by_depth[d])

    outdegree_by_depth: dict[int, Counter[int]] = defaultdict(Counter)
    for node in nodes.values():
        d = int(node["min_depth"])
        outdegree_by_depth[d][len(node.get("children", []))] += 1
    entropy_branching = {
        str(d): _entropy(counter) for d, counter in sorted(outdegree_by_depth.items(), key=lambda x: x[0])
    }

    sig_growth_rate = {}
    for d in depths:
        nd = nodes_by_depth.get(d, 0)
        ud = unique_by_depth.get(d, 0)
        sig_growth_rate[str(d)] = (ud / nd) if nd > 0 else 0.0

    return {
        "growth_rate_log": growth_rate,
        "branching_entropy": entropy_branching,
        "signature_growth_rate": sig_growth_rate,
    }


def _micro_motif_descriptor(
    graph: dict[str, Any],
    node_sigs: dict[str, str],
    neighbors: dict[str, set[str]],
    outgoing: dict[str, list[dict[str, Any]]],
    center: str,
    radius: int,
) -> str:
    q = deque([(center, 0)])
    seen = {center}
    shell = defaultdict(Counter)
    while q:
        cur, d = q.popleft()
        shell[d][node_sigs.get(cur, "NA")] += 1
        if d >= radius:
            continue
        for nb in neighbors.get(cur, set()):
            if nb not in seen:
                seen.add(nb)
                q.append((nb, d + 1))

    center_transitions = []
    for e in outgoing.get(center, []):
        center_transitions.append(
            [int(e["a"]), node_sigs.get(str(e["target"]), "NA"), str(e.get("kind", ""))]
        )
    center_transitions.sort(key=lambda x: (x[0], x[1], x[2]))
    shell_json = {
        str(d): {k: int(v) for k, v in sorted(c.items(), key=lambda x: x[0])}
        for d, c in sorted(shell.items(), key=lambda x: x[0])
    }
    payload = {
        "center_sig": node_sigs.get(center, "NA"),
        "shells": shell_json,
        "center_transitions": center_transitions,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def micro_alignment_test(
    source_automaton: dict[str, Any],
    target_automaton: dict[str, Any],
    radius: int = 2,
    sample_size: int = 120,
    max_examples: int = 30,
) -> dict[str, Any]:
    src_graph = source_automaton["graph"]
    tgt_graph = target_automaton["graph"]
    src_sigs: dict[str, str] = source_automaton["signatures"]["node_signatures"]
    tgt_sigs: dict[str, str] = target_automaton["signatures"]["node_signatures"]

    src_out, src_nb = _edge_maps(src_graph)
    tgt_out, tgt_nb = _edge_maps(tgt_graph)

    target_descs = set()
    for node_id in tgt_graph["nodes"].keys():
        desc = _micro_motif_descriptor(tgt_graph, tgt_sigs, tgt_nb, tgt_out, node_id, radius)
        target_descs.add(desc)

    src_nodes = sorted(src_graph["nodes"].keys(), key=lambda nid: int(src_graph["nodes"][nid]["value"]))
    if len(src_nodes) > sample_size:
        step = len(src_nodes) / sample_size
        sampled = [src_nodes[min(len(src_nodes) - 1, int(i * step))] for i in range(sample_size)]
    else:
        sampled = src_nodes

    matched = 0
    examples = []
    for node_id in sampled:
        desc = _micro_motif_descriptor(src_graph, src_sigs, src_nb, src_out, node_id, radius)
        if desc in target_descs:
            matched += 1
            if len(examples) < max_examples:
                examples.append(
                    {
                        "node_id": node_id,
                        "value": int(src_graph["nodes"][node_id]["value"]),
                        "depth": int(src_graph["nodes"][node_id]["min_depth"]),
                    }
                )

    ratio = (matched / len(sampled)) if sampled else 0.0
    return {
        "source_root": source_automaton["root_label"],
        "target_root": target_automaton["root_label"],
        "radius": radius,
        "sample_size": len(sampled),
        "matched_subgraphs": matched,
        "match_ratio": ratio,
        "matched_examples": examples,
    }


def analyze_automata_diff(
    left_automaton: dict[str, Any],
    right_automaton: dict[str, Any],
    max_items: int = 250,
    motif_radius: int = 2,
) -> dict[str, Any]:
    base_cmp = compare_automata(left_automaton, right_automaton, normalize_depth=True)
    first_div = find_first_divergence(left_automaton, right_automaton, max_items=max_items)

    motifs_a = [
        extract_local_motif(
            left_automaton,
            signature=sig,
            depth=first_div["depth"],
            radius=motif_radius,
        )
        for sig in first_div["only_in_A"][: min(40, len(first_div["only_in_A"]))]
    ]
    motifs_b = [
        extract_local_motif(
            right_automaton,
            signature=sig,
            depth=first_div["depth"],
            radius=motif_radius,
        )
        for sig in first_div["only_in_B"][: min(40, len(first_div["only_in_B"]))]
    ]

    transition_diff = compare_signature_transitions(
        left_automaton,
        right_automaton,
        max_items=max_items,
    )
    grammar_diff = compare_grammar_rules(
        left_automaton,
        right_automaton,
        max_items=max_items,
    )

    shape_left = _shape_metrics(left_automaton)
    shape_right = _shape_metrics(right_automaton)

    depth_profile_similarity = float(base_cmp["comparison"]["rescaled_depth_profile_cosine"])
    signature_jaccard = float(base_cmp["comparison"]["signature_jaccard"])
    transition_overlap = float(transition_diff["transition_overlap_ratio"])
    rule_overlap = float(grammar_diff["rule_overlap_ratio"])

    structural_similarity_score = (
        0.35 * signature_jaccard
        + 0.25 * transition_overlap
        + 0.25 * rule_overlap
        + 0.15 * depth_profile_similarity
    )

    # For the research ask: probe whether local pieces of 27 appear inside xstar.
    if left_automaton["root_label"] == "xstar" and right_automaton["root_label"] in ("27", "121"):
        micro = micro_alignment_test(
            source_automaton=right_automaton,
            target_automaton=left_automaton,
            radius=motif_radius,
        )
    elif right_automaton["root_label"] == "xstar" and left_automaton["root_label"] in ("27", "121"):
        micro = micro_alignment_test(
            source_automaton=left_automaton,
            target_automaton=right_automaton,
            radius=motif_radius,
        )
    else:
        # Generic fallback: smaller into larger
        if left_automaton["graph"]["meta"]["node_count"] <= right_automaton["graph"]["meta"]["node_count"]:
            micro = micro_alignment_test(
                source_automaton=left_automaton,
                target_automaton=right_automaton,
                radius=motif_radius,
            )
        else:
            micro = micro_alignment_test(
                source_automaton=right_automaton,
                target_automaton=left_automaton,
                radius=motif_radius,
            )

    return {
        "left_root": left_automaton["root_label"],
        "right_root": right_automaton["root_label"],
        "alignment": {
            "depth": int(left_automaton["graph"]["meta"]["max_depth"]),
            "max_bits": left_automaton["graph"]["meta"]["max_bits"],
            "a_max": int(left_automaton["graph"]["meta"]["a_max"]),
            "normalize_depth": True,
        },
        "base_comparison": base_cmp,
        "first_divergence": first_div,
        "local_motifs": {
            "only_in_A": motifs_a,
            "only_in_B": motifs_b,
        },
        "signature_transitions": transition_diff,
        "grammar_difference": grammar_diff,
        "normalized_shape": {
            "left": shape_left,
            "right": shape_right,
        },
        "micro_alignment": micro,
        "summary": {
            "first_divergence_depth": first_div["depth"],
            "rule_overlap_ratio": rule_overlap,
            "transition_overlap_ratio": transition_overlap,
            "depth_profile_similarity": depth_profile_similarity,
            "signature_jaccard": signature_jaccard,
            "structural_similarity_score": structural_similarity_score,
        },
    }


def save_diff_analysis(data: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

