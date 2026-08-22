from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automaton_compare import compare_automata
from preimage_automaton import build_preimage_automaton


def collect_seed_numbers() -> list[int]:
    numbers: set[int] = set()

    try:
        import records_data

        for n in records_data.get_all_as_int():
            if n > 0:
                numbers.add(int(n))
    except Exception:
        pass

    for name in ("dist/extra_seeds.json", "dist/extra_seeds1.json"):
        path = Path(name)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for row in data.get("seeds", []):
                b = row.get("binary")
                if isinstance(b, str) and b:
                    numbers.add(int(b, 2))
        except Exception:
            continue

    return sorted(numbers)


def _path_to_root(graph: dict[str, Any], node_id: str) -> dict[str, Any]:
    nodes = graph["nodes"]
    if node_id not in nodes:
        return {"values": [], "edges": []}

    values = []
    edges = []
    cur = node_id
    while True:
        node = nodes[cur]
        values.append(int(node["value"]))
        parent_id = node.get("representative_parent_id")
        incoming_a = node.get("representative_incoming_a")
        if parent_id is None:
            break
        edges.append({"parent_id": str(parent_id), "child_id": cur, "a": incoming_a})
        cur = str(parent_id)
        if cur not in nodes:
            break
    values.reverse()
    edges.reverse()
    return {"values": values, "edges": edges}


def find_graph_candidates(
    bundle: dict[str, Any],
    target_signature: str | None = None,
    limit: int = 100,
    min_depth: int = 1,
) -> list[dict[str, Any]]:
    graph = bundle["graph"]
    node_signatures = bundle["signatures"]["node_signatures"]
    target_sig = target_signature or bundle["signatures"]["root_signature"]

    hits = []
    for node_id, sig in node_signatures.items():
        if sig != target_sig:
            continue
        node = graph["nodes"][node_id]
        if int(node["min_depth"]) < min_depth:
            continue
        path = _path_to_root(graph, node_id)
        hits.append(
            {
                "node_id": node_id,
                "value": int(node["value"]),
                "bit_length": int(node["bit_length"]),
                "depth": int(node["min_depth"]),
                "parents_count": len(node.get("parents", [])),
                "children_count": len(node.get("children", [])),
                "path_to_root": path,
            }
        )

    hits.sort(key=lambda r: (r["depth"], r["bit_length"], r["value"]))
    return hits[:limit]


def search_external_candidates(
    target_bundle: dict[str, Any],
    depth: int,
    max_bits: int | None,
    a_max: int,
    limit: int = 50,
    similarity_threshold: float = 0.72,
) -> dict[str, Any]:
    target_sig = target_bundle["signatures"]["root_signature"]
    target_value = int(target_bundle["root_value"])
    seeds = collect_seed_numbers()

    rows: list[dict[str, Any]] = []
    exact_hits: list[dict[str, Any]] = []
    scaled_hits: list[dict[str, Any]] = []
    checked = 0

    for n in seeds:
        if checked >= limit:
            break
        if n <= 0 or n == target_value:
            continue
        if max_bits is not None and n.bit_length() > max_bits:
            continue
        checked += 1

        cand_bundle = build_preimage_automaton(
            root=n,
            max_depth=depth,
            max_bits=max_bits if max_bits is not None else n.bit_length() + 45,
            a_max=a_max,
            minimize=True,
            include_forward_summary=False,
        )
        comp = compare_automata(target_bundle, cand_bundle, normalize_depth=True)
        score = float(comp["comparison"]["similarity_score"])
        same_class = cand_bundle["signatures"]["root_signature"] == target_sig

        row = {
            "n": str(n),
            "bits": n.bit_length(),
            "signature": cand_bundle["signatures"]["root_signature"],
            "same_signature_class": same_class,
            "similarity_score": score,
            "verdict": comp["comparison"]["verdict"],
            "depth_of_first_divergence": comp["comparison"]["depth_of_first_divergence"],
        }
        rows.append(row)
        if same_class:
            exact_hits.append(row)
        if score >= similarity_threshold:
            scaled_hits.append(row)

    rows.sort(key=lambda r: r["similarity_score"], reverse=True)
    exact_hits.sort(key=lambda r: (r["bits"], int(r["n"])))
    scaled_hits.sort(key=lambda r: r["similarity_score"], reverse=True)

    return {
        "checked_candidates": checked,
        "same_signature_class": exact_hits,
        "scaled_analogues": scaled_hits[: min(200, len(scaled_hits))],
        "all_ranked": rows[: min(500, len(rows))],
    }


def run_candidate_search(
    target_bundle: dict[str, Any],
    depth: int,
    max_bits: int | None,
    a_max: int,
    limit: int = 50,
    similarity_threshold: float = 0.72,
    graph_limit: int = 200,
) -> dict[str, Any]:
    target_sig = target_bundle["signatures"]["root_signature"]
    in_graph = find_graph_candidates(
        target_bundle,
        target_signature=target_sig,
        limit=graph_limit,
        min_depth=1,
    )
    external = search_external_candidates(
        target_bundle=target_bundle,
        depth=depth,
        max_bits=max_bits,
        a_max=a_max,
        limit=limit,
        similarity_threshold=similarity_threshold,
    )
    return {
        "target_root_label": target_bundle["root_label"],
        "target_root_value": target_bundle["root_value"],
        "target_root_signature": target_sig,
        "in_graph_same_signature_candidates": in_graph,
        **external,
    }

