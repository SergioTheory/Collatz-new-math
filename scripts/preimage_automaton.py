from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automaton_signatures import compute_signatures
from reverse_graph_builder import build_reverse_graph, resolve_root


def _compute_basic_graph_stats(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph["nodes"]
    edges = graph["edges"]

    nodes_by_depth: dict[str, int] = {}
    for depth, node_ids in graph["depth_index"].items():
        nodes_by_depth[str(depth)] = len(node_ids)

    outdegree_dist: dict[str, int] = {}
    indegree_dist: dict[str, int] = {}
    for node in nodes.values():
        outd = len(node.get("children", []))
        ind = len(node.get("parents", []))
        outdegree_dist[str(outd)] = outdegree_dist.get(str(outd), 0) + 1
        indegree_dist[str(ind)] = indegree_dist.get(str(ind), 0) + 1

    shift_dist: dict[str, int] = {}
    for edge in edges:
        key = str(int(edge["a"]))
        shift_dist[key] = shift_dist.get(key, 0) + 1

    merge_nodes = sum(1 for node in nodes.values() if len(node.get("parents", [])) > 1)
    max_indegree_node = None
    max_indegree = -1
    for node in nodes.values():
        deg = len(node.get("parents", []))
        if deg > max_indegree:
            max_indegree = deg
            max_indegree_node = node["id"]

    return {
        "nodes_by_depth": nodes_by_depth,
        "outdegree_distribution": outdegree_dist,
        "indegree_distribution": indegree_dist,
        "shift_distribution": dict(sorted(shift_dist.items(), key=lambda x: int(x[0]))),
        "confluence": {
            "merge_nodes": int(merge_nodes),
            "max_indegree": int(max_indegree),
            "max_indegree_node": str(max_indegree_node) if max_indegree_node is not None else None,
        },
    }


def build_preimage_automaton(
    root: str | int,
    max_depth: int,
    max_bits: int | None,
    a_max: int,
    minimize: bool = True,
    include_forward_summary: bool = False,
) -> dict[str, Any]:
    root_label, root_value = resolve_root(root)
    graph = build_reverse_graph(
        root_value=root_value,
        max_depth=max_depth,
        max_bits=max_bits,
        a_max=a_max,
        include_forward_summary=include_forward_summary,
    )
    signature_info = compute_signatures(graph)
    basic_stats = _compute_basic_graph_stats(graph)

    result = {
        "root_label": root_label,
        "root_value": root_value,
        "graph": graph,
        "signatures": signature_info,
        "summary": {
            **basic_stats,
            "node_count": int(graph["meta"]["node_count"]),
            "edge_count": int(graph["meta"]["edge_count"]),
            "unique_signatures": len(signature_info["signature_multiset"]),
            "root_signature": signature_info["root_signature"],
        },
    }
    if not minimize:
        result["signatures"]["minimized"] = None
    return result


def save_automaton(bundle: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_automaton(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

