from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any


def _stable_hash(payload: dict[str, Any]) -> str:
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()[:24]


def compute_signatures(graph: dict[str, Any], include_payloads: bool = False) -> dict[str, Any]:
    """
    Canonical subtree signatures for reverse-preimage DAG.
    Signature is computed bottom-up by depth.
    """
    nodes: dict[str, dict[str, Any]] = graph["nodes"]
    edges: list[dict[str, Any]] = graph["edges"]
    max_depth = int(graph["meta"]["max_depth"])
    root_bits = int(graph["meta"]["root_bits"])

    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        outgoing[str(edge["source"])].append(edge)

    for edge_list in outgoing.values():
        edge_list.sort(key=lambda e: (int(e["a"]), str(e["target"]), str(e["kind"])))

    # Descending depth ensures children are already hashed.
    ordered_node_ids = sorted(
        nodes.keys(),
        key=lambda nid: (int(nodes[nid]["min_depth"]), int(nodes[nid]["value"])),
        reverse=True,
    )

    node_signatures: dict[str, str] = {}
    payloads: dict[str, dict[str, Any]] = {}

    for node_id in ordered_node_ids:
        node = nodes[node_id]
        node_out = outgoing.get(node_id, [])
        child_signature_pairs: list[tuple[int, str, str]] = []
        for edge in node_out:
            child_id = str(edge["target"])
            child_sig = node_signatures.get(child_id, "LEAF")
            child_signature_pairs.append((int(edge["a"]), child_sig, str(edge["kind"])))

        child_multiset = Counter(sig for _, sig, _ in child_signature_pairs)
        shift_multiset = Counter(a for a, _, _ in child_signature_pairs)

        depth = int(node["min_depth"])
        depth_norm = (depth / max_depth) if max_depth > 0 else 0.0
        rem_depth_norm = ((max_depth - depth) / max_depth) if max_depth > 0 else 0.0

        residues = node.get("residues", {})
        payload = {
            "bit_delta": int(node["bit_length"]) - root_bits,
            "bit_length": int(node["bit_length"]),
            "depth": depth,
            "depth_norm": round(depth_norm, 6),
            "remaining_depth_norm": round(rem_depth_norm, 6),
            "child_signature_multiset": sorted(
                [[sig, int(cnt)] for sig, cnt in child_multiset.items()],
                key=lambda x: (x[0], x[1]),
            ),
            "outgoing_labels": sorted(
                [[int(a), int(cnt)] for a, cnt in shift_multiset.items()],
                key=lambda x: (x[0], x[1]),
            ),
            "outgoing_labeled_children": [
                [int(a), child_sig, kind] for a, child_sig, kind in child_signature_pairs
            ],
            "residue_profile": residues,
        }
        sig = _stable_hash(payload)
        node_signatures[node_id] = sig
        if include_payloads:
            payloads[node_id] = payload

    signature_multiset = Counter(node_signatures.values())
    depth_signature_multiset: dict[str, dict[str, int]] = {}
    for node_id, sig in node_signatures.items():
        d = str(nodes[node_id]["min_depth"])
        depth_signature_multiset.setdefault(d, {})
        depth_signature_multiset[d][sig] = depth_signature_multiset[d].get(sig, 0) + 1

    # Minimized automaton.
    sig_to_state_id: dict[str, str] = {}
    for idx, sig in enumerate(sorted(signature_multiset.keys()), start=1):
        sig_to_state_id[sig] = f"s{idx:05d}"

    state_nodes: dict[str, list[str]] = defaultdict(list)
    for node_id, sig in node_signatures.items():
        state_nodes[sig].append(node_id)

    states: dict[str, dict[str, Any]] = {}
    for sig, node_ids in state_nodes.items():
        node_ids_sorted = sorted(node_ids, key=lambda nid: int(nodes[nid]["value"]))
        depth_hist = Counter(int(nodes[nid]["min_depth"]) for nid in node_ids_sorted)
        bit_lengths = [int(nodes[nid]["bit_length"]) for nid in node_ids_sorted]
        states[sig_to_state_id[sig]] = {
            "signature": sig,
            "node_count": len(node_ids_sorted),
            "depth_histogram": {str(k): int(v) for k, v in sorted(depth_hist.items())},
            "bit_length_min": min(bit_lengths),
            "bit_length_max": max(bit_lengths),
            "sample_nodes": node_ids_sorted[:20],
        }

    trans_counter: Counter[tuple[str, str, int, str]] = Counter()
    for edge in edges:
        src = str(edge["source"])
        tgt = str(edge["target"])
        a = int(edge["a"])
        kind = str(edge["kind"])
        src_state = sig_to_state_id[node_signatures[src]]
        tgt_state = sig_to_state_id[node_signatures[tgt]]
        trans_counter[(src_state, tgt_state, a, kind)] += 1

    transitions = [
        {
            "source_state": src,
            "target_state": tgt,
            "a": int(a),
            "kind": kind,
            "count": int(cnt),
        }
        for (src, tgt, a, kind), cnt in sorted(trans_counter.items())
    ]

    root_id = str(graph["root_id"])
    root_signature = node_signatures[root_id]
    root_state_id = sig_to_state_id[root_signature]

    return {
        "root_signature": root_signature,
        "root_state_id": root_state_id,
        "node_signatures": node_signatures,
        "node_signature_payloads": payloads if include_payloads else {},
        "signature_multiset": dict(signature_multiset),
        "depth_signature_multiset": depth_signature_multiset,
        "minimized": {
            "states": states,
            "transitions": transitions,
            "state_count": len(states),
            "transition_count": len(transitions),
        },
    }
