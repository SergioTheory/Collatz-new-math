from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

DIST_DIR = Path(__file__).resolve().parent / "dist"
if DIST_DIR.exists() and str(DIST_DIR) not in sys.path:
    sys.path.insert(0, str(DIST_DIR))

try:
    from crt_solver import analyze_to_peak, collatz_peak
except Exception:  # pragma: no cover - fallback for minimal environments
    analyze_to_peak = None
    collatz_peak = None

XSTAR_VALUE = 20152090995747160937051
CENTER_27_VALUE = 121  # x7 for trajectory of 27
BARINA_VALUE = 1765856170146672440559

ROOT_ALIASES: dict[str, tuple[str, int]] = {
    "xstar": ("xstar", XSTAR_VALUE),
    "zone2": ("xstar", XSTAR_VALUE),
    "27": ("27", CENTER_27_VALUE),
    "x7": ("27", CENTER_27_VALUE),
    "121": ("27", CENTER_27_VALUE),
    "barina": ("barina", BARINA_VALUE),
}


def resolve_root(root: str | int) -> tuple[str, int]:
    """Resolve canonical root alias or custom integer."""
    if isinstance(root, int):
        if root <= 0:
            raise ValueError("root must be positive")
        return f"custom_{root}", root

    text = str(root).strip().lower()
    if text in ROOT_ALIASES:
        return ROOT_ALIASES[text]
    if text.isdigit():
        value = int(text)
        if value <= 0:
            raise ValueError("root must be positive")
        return f"custom_{value}", value
    raise ValueError(
        f"Unknown root '{root}'. Use xstar | 27 | barina | positive integer."
    )


def _make_residues(value: int, residue_moduli: tuple[int, ...]) -> dict[str, int]:
    return {str(m): int(value % m) for m in residue_moduli}


def find_reverse_predecessors(
    m: int,
    a_max: int,
    max_bits: int | None = None,
    include_double: bool = True,
) -> list[dict[str, int | str]]:
    """
    Reverse candidates for accelerated Collatz dynamics.
    1) always candidate 2m;
    2) candidates (2^a * m - 1) / 3 for a=1..a_max if odd positive integer.
    """
    if m <= 0:
        return []

    preds: list[dict[str, int | str]] = []

    if include_double:
        n2 = m * 2
        if max_bits is None or n2.bit_length() <= max_bits:
            preds.append({"value": n2, "a": 0, "kind": "double"})

    for a in range(1, a_max + 1):
        val = (m << a) - 1
        if val % 3 != 0:
            continue
        n = val // 3
        if n <= 0 or (n & 1) == 0:
            continue
        if max_bits is not None and n.bit_length() > max_bits:
            continue
        preds.append({"value": n, "a": a, "kind": "odd_preimage"})

    return preds


def build_reverse_graph(
    root_value: int,
    max_depth: int,
    max_bits: int | None,
    a_max: int,
    include_forward_summary: bool = False,
    residue_moduli: tuple[int, ...] = (3, 8, 16),
) -> dict[str, Any]:
    """
    Build reverse-preimage DAG with deduplication by integer value.
    """
    if root_value <= 0:
        raise ValueError("root_value must be positive")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if a_max < 1:
        raise ValueError("a_max must be >= 1")

    root_id = str(root_value)
    nodes: dict[str, dict[str, Any]] = {
        root_id: {
            "id": root_id,
            "value": root_value,
            "bit_length": root_value.bit_length(),
            "min_depth": 0,
            "depths": {0},
            "incoming": [],
            "parents": set(),
            "children": set(),
            "path_signature": "",
            "path_length": 0,
            "representative_parent_id": None,
            "representative_incoming_a": None,
            "residues": _make_residues(root_value, residue_moduli),
        }
    }
    edges: list[dict[str, Any]] = []
    edge_set: set[tuple[str, str, int, str]] = set()
    depth_index: dict[int, set[str]] = {0: {root_id}}

    frontier: list[str] = [root_id]
    for depth in range(max_depth):
        next_frontier: list[str] = []
        for parent_id in frontier:
            parent = nodes[parent_id]
            parent_val = int(parent["value"])
            parent_sig = str(parent.get("path_signature", ""))
            parent_len = int(parent.get("path_length", 0))

            for pred in find_reverse_predecessors(
                parent_val,
                a_max=a_max,
                max_bits=max_bits,
                include_double=True,
            ):
                child_value = int(pred["value"])
                child_id = str(child_value)
                edge_a = int(pred["a"])
                edge_kind = str(pred["kind"])
                edge_key = (parent_id, child_id, edge_a, edge_kind)

                if child_id not in nodes:
                    nodes[child_id] = {
                        "id": child_id,
                        "value": child_value,
                        "bit_length": child_value.bit_length(),
                        "min_depth": depth + 1,
                        "depths": {depth + 1},
                        "incoming": [],
                        "parents": set(),
                        "children": set(),
                        "path_signature": f"{parent_sig}.{edge_a}" if parent_sig else str(edge_a),
                        "path_length": parent_len + 1,
                        "representative_parent_id": parent_id,
                        "representative_incoming_a": edge_a,
                        "residues": _make_residues(child_value, residue_moduli),
                    }
                    next_frontier.append(child_id)
                    depth_index.setdefault(depth + 1, set()).add(child_id)
                else:
                    nodes[child_id]["depths"].add(depth + 1)
                    depth_index.setdefault(depth + 1, set()).add(child_id)

                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append(
                        {
                            "source": parent_id,
                            "target": child_id,
                            "a": edge_a,
                            "kind": edge_kind,
                            "depth": depth + 1,
                        }
                    )

                nodes[parent_id]["children"].add(child_id)
                nodes[child_id]["parents"].add(parent_id)
                nodes[child_id]["incoming"].append(
                    {"parent_id": parent_id, "a": edge_a, "kind": edge_kind}
                )

        frontier = sorted(set(next_frontier), key=lambda x: int(x))
        if not frontier:
            break

    if include_forward_summary and analyze_to_peak is not None and collatz_peak is not None:
        for node in nodes.values():
            n = int(node["value"])
            try:
                info = analyze_to_peak(n, max_steps=500_000)
                peak_bits, steps_done, converged = collatz_peak(n, max_steps=500_000)
                node["forward_summary"] = {
                    "peak": int(info.get("peak", peak_bits)),
                    "peak_step": int(info.get("peak_step", 0)),
                    "total_o": int(info.get("total_o", 0)),
                    "total_e": int(info.get("total_e", 0)),
                    "gain": float(info.get("gain", 0.0)),
                    "collatz_peak_bits": int(peak_bits),
                    "collatz_steps_done": int(steps_done),
                    "collatz_converged": bool(converged),
                }
            except Exception:
                node["forward_summary"] = None

    nodes_out: dict[str, dict[str, Any]] = {}
    for node_id, node in nodes.items():
        nodes_out[node_id] = {
            **node,
            "parents": sorted(node["parents"], key=lambda x: int(x)),
            "children": sorted(node["children"], key=lambda x: int(x)),
            "depths": sorted(node["depths"]),
        }

    depth_index_out = {
        str(depth): sorted(node_ids, key=lambda x: int(x))
        for depth, node_ids in sorted(depth_index.items(), key=lambda x: x[0])
    }

    return {
        "meta": {
            "root_value": int(root_value),
            "root_bits": int(root_value.bit_length()),
            "max_depth": int(max_depth),
            "max_bits": int(max_bits) if max_bits is not None else None,
            "a_max": int(a_max),
            "include_forward_summary": bool(include_forward_summary),
            "residue_moduli": list(residue_moduli),
            "node_count": len(nodes_out),
            "edge_count": len(edges),
        },
        "root_id": root_id,
        "nodes": nodes_out,
        "edges": edges,
        "depth_index": depth_index_out,
    }
