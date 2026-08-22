from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def export_json(data: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def export_graph_csv(graph: dict[str, Any], out_dir: str | Path, prefix: str) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = out_dir / f"{prefix}_nodes.csv"
    edges_path = out_dir / f"{prefix}_edges.csv"

    with nodes_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "value",
                "bit_length",
                "min_depth",
                "depths",
                "parents_count",
                "children_count",
                "path_signature",
            ],
        )
        writer.writeheader()
        for node in graph["nodes"].values():
            writer.writerow(
                {
                    "id": node["id"],
                    "value": node["value"],
                    "bit_length": node["bit_length"],
                    "min_depth": node["min_depth"],
                    "depths": ";".join(str(d) for d in node["depths"]),
                    "parents_count": len(node.get("parents", [])),
                    "children_count": len(node.get("children", [])),
                    "path_signature": node.get("path_signature", ""),
                }
            )

    with edges_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "a", "kind", "depth"])
        writer.writeheader()
        for edge in graph["edges"]:
            writer.writerow(edge)

    return nodes_path, edges_path


def export_graphml(graph: dict[str, Any], path: str | Path) -> Path:
    import networkx as nx

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    g = nx.DiGraph()
    for node in graph["nodes"].values():
        g.add_node(
            node["id"],
            value=int(node["value"]),
            bit_length=int(node["bit_length"]),
            min_depth=int(node["min_depth"]),
        )
    for edge in graph["edges"]:
        g.add_edge(
            edge["source"],
            edge["target"],
            a=int(edge["a"]),
            kind=str(edge["kind"]),
            depth=int(edge["depth"]),
        )

    nx.write_graphml(g, path)
    return path


def export_gexf(graph: dict[str, Any], path: str | Path) -> Path:
    import networkx as nx

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    g = nx.DiGraph()
    for node in graph["nodes"].values():
        g.add_node(
            node["id"],
            value=int(node["value"]),
            bit_length=int(node["bit_length"]),
            min_depth=int(node["min_depth"]),
        )
    for edge in graph["edges"]:
        g.add_edge(
            edge["source"],
            edge["target"],
            a=int(edge["a"]),
            kind=str(edge["kind"]),
            depth=int(edge["depth"]),
        )

    nx.write_gexf(g, path)
    return path


def plot_layered_dag(graph: dict[str, Any], path: str | Path, title: str) -> Path:
    import matplotlib.pyplot as plt
    import networkx as nx

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    g = nx.DiGraph()
    for node in graph["nodes"].values():
        g.add_node(node["id"], depth=int(node["min_depth"]))
    for edge in graph["edges"]:
        g.add_edge(edge["source"], edge["target"], a=int(edge["a"]))

    layers: dict[int, list[str]] = defaultdict(list)
    for node_id, data in g.nodes(data=True):
        layers[int(data["depth"])].append(node_id)
    for depth in layers:
        layers[depth].sort(key=lambda nid: int(nid))

    pos = {}
    for depth, node_ids in sorted(layers.items()):
        width = max(1, len(node_ids) - 1)
        for idx, nid in enumerate(node_ids):
            x = idx / width if width else 0.0
            y = -depth
            pos[nid] = (x, y)

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(g, pos, node_size=30, alpha=0.8)
    nx.draw_networkx_edges(g, pos, arrows=False, width=0.4, alpha=0.35)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_layered_dag_colored(
    graph: dict[str, Any],
    path: str | Path,
    title: str,
    color_by: str = "depth",
    node_to_signature: dict[str, str] | None = None,
) -> Path:
    import hashlib
    import matplotlib.pyplot as plt
    import networkx as nx

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    g = nx.DiGraph()
    for node in graph["nodes"].values():
        g.add_node(node["id"], depth=int(node["min_depth"]))
    for edge in graph["edges"]:
        g.add_edge(edge["source"], edge["target"], a=int(edge["a"]))

    layers: dict[int, list[str]] = defaultdict(list)
    for node_id, data in g.nodes(data=True):
        layers[int(data["depth"])].append(node_id)
    for depth in layers:
        layers[depth].sort(key=lambda nid: int(nid))

    pos = {}
    for depth, node_ids in sorted(layers.items()):
        width = max(1, len(node_ids) - 1)
        for idx, nid in enumerate(node_ids):
            x = idx / width if width else 0.0
            y = -depth
            pos[nid] = (x, y)

    if color_by == "signature" and node_to_signature:
        cmap = plt.get_cmap("tab20")
        colors = []
        for nid in g.nodes():
            sig = node_to_signature.get(nid, "none")
            bucket = int(hashlib.sha1(sig.encode("utf-8")).hexdigest()[:6], 16) % 20
            colors.append(cmap(bucket / 19))
    else:
        depths = [int(g.nodes[n]["depth"]) for n in g.nodes()]
        max_depth = max(depths) if depths else 1
        cmap = plt.get_cmap("viridis")
        colors = [cmap(d / max_depth if max_depth > 0 else 0.0) for d in depths]

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(g, pos, node_size=30, alpha=0.9, node_color=colors)
    nx.draw_networkx_edges(g, pos, arrows=False, width=0.4, alpha=0.30)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_depth_heatmap(graph: dict[str, Any], path: str | Path, title: str) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    xs = []
    ys = []
    for node in graph["nodes"].values():
        xs.append(int(node["min_depth"]))
        ys.append(int(node["bit_length"]))

    plt.figure(figsize=(10, 6))
    if xs and ys:
        plt.hist2d(xs, ys, bins=[max(xs) + 1, max(5, min(50, len(set(ys))))], cmap="viridis")
        plt.colorbar(label="count")
    plt.xlabel("depth")
    plt.ylabel("bit_length")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_series_by_depth(
    values: dict[str, int | float],
    path: str | Path,
    title: str,
    y_label: str,
    cumulative: bool = False,
) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    points = sorted(((int(k), float(v)) for k, v in values.items()), key=lambda x: x[0])
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if cumulative:
        run = 0.0
        ys_cum = []
        for y in ys:
            run += y
            ys_cum.append(run)
        ys = ys_cum

    plt.figure(figsize=(10, 5))
    plt.plot(xs, ys, marker="o")
    plt.xlabel("depth")
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_shift_histogram(graph: dict[str, Any], path: str | Path, title: str) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    counter = Counter(int(edge["a"]) for edge in graph["edges"])
    xs = sorted(counter.keys())
    ys = [counter[x] for x in xs]

    plt.figure(figsize=(10, 5))
    plt.bar(xs, ys, color="#2878b5")
    plt.xlabel("shift label a")
    plt.ylabel("count")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_signature_overlap_matrix(
    metrics_list: list[dict[str, Any]],
    path: str | Path,
    title: str = "Signature Overlap Matrix",
) -> Path:
    import matplotlib.pyplot as plt
    import numpy as np

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    labels = [m["root_label"] for m in metrics_list]
    sig_sets = [set(m.get("signature_multiset", {}).keys()) for m in metrics_list]
    n = len(sig_sets)
    mat = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            u = sig_sets[i] | sig_sets[j]
            inter = sig_sets[i] & sig_sets[j]
            mat[i, j] = (len(inter) / len(u)) if u else 1.0

    fig, ax = plt.subplots(figsize=(6 + n, 5 + n * 0.3))
    im = ax.imshow(mat, cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_xticks(range(n), labels=labels, rotation=30, ha="right")
    ax.set_yticks(range(n), labels=labels)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=8)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_multi_branch_growth(
    metrics_list: list[dict[str, Any]],
    path: str | Path,
    title: str = "Branch Growth N(depth)",
) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(11, 6))
    for m in metrics_list:
        points = sorted(
            ((int(k), int(v)) for k, v in m.get("nodes_by_depth", {}).items()),
            key=lambda x: x[0],
        )
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        plt.plot(xs, ys, marker="o", label=m["root_label"])
    plt.xlabel("depth")
    plt.ylabel("N(depth)")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_comparison(
    left_metrics: dict[str, Any],
    right_metrics: dict[str, Any],
    path: str | Path,
    title: str,
) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    left_depth = {int(k): int(v) for k, v in left_metrics["nodes_by_depth"].items()}
    right_depth = {int(k): int(v) for k, v in right_metrics["nodes_by_depth"].items()}
    left_shift = {int(k): int(v) for k, v in left_metrics["shift_distribution"].items()}
    right_shift = {int(k): int(v) for k, v in right_metrics["shift_distribution"].items()}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    x1 = sorted(left_depth.keys())
    y1 = [left_depth[k] for k in x1]
    x2 = sorted(right_depth.keys())
    y2 = [right_depth[k] for k in x2]
    axes[0].plot(x1, y1, marker="o", label=left_metrics["root_label"])
    axes[0].plot(x2, y2, marker="o", label=right_metrics["root_label"])
    axes[0].set_xlabel("depth")
    axes[0].set_ylabel("nodes")
    axes[0].set_title("Branch Growth by Depth")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    shift_keys = sorted(set(left_shift.keys()) | set(right_shift.keys()))
    left_vals = [left_shift.get(k, 0) for k in shift_keys]
    right_vals = [right_shift.get(k, 0) for k in shift_keys]
    w = 0.4
    axes[1].bar([x - w / 2 for x in shift_keys], left_vals, width=w, label=left_metrics["root_label"])
    axes[1].bar([x + w / 2 for x in shift_keys], right_vals, width=w, label=right_metrics["root_label"])
    axes[1].set_xlabel("shift label a")
    axes[1].set_ylabel("count")
    axes[1].set_title("Shift Distribution")
    axes[1].legend()

    fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_signature_tree(bundle: dict[str, Any], path: str | Path, title: str) -> Path:
    import matplotlib.pyplot as plt
    import networkx as nx

    minimized = bundle["signatures"].get("minimized")
    if not minimized:
        raise ValueError("No minimized automaton available to plot signature tree")

    states = minimized["states"]
    transitions = minimized["transitions"]

    # Keep visualization readable for very large automata.
    ranked_states = sorted(
        states.items(),
        key=lambda kv: kv[1].get("node_count", 0),
        reverse=True,
    )
    keep = {sid for sid, _ in ranked_states[:120]}
    root_state = bundle["signatures"]["root_state_id"]
    keep.add(root_state)

    g = nx.DiGraph()
    for sid, state in states.items():
        if sid not in keep:
            continue
        depth_hist = {int(k): int(v) for k, v in state.get("depth_histogram", {}).items()}
        min_depth = min(depth_hist.keys()) if depth_hist else 0
        g.add_node(sid, size=max(30, 20 + state["node_count"] * 2), depth=min_depth)
    for tr in transitions:
        s = tr["source_state"]
        t = tr["target_state"]
        if s in keep and t in keep:
            g.add_edge(s, t, a=int(tr["a"]), w=max(0.2, tr["count"] ** 0.4))

    layers: dict[int, list[str]] = defaultdict(list)
    for nid, data in g.nodes(data=True):
        layers[int(data.get("depth", 0))].append(nid)
    for d in layers:
        layers[d].sort()

    pos = {}
    for d, node_ids in sorted(layers.items()):
        width = max(1, len(node_ids) - 1)
        for i, nid in enumerate(node_ids):
            pos[nid] = (i / width if width else 0.0, -d)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(
        g,
        pos,
        node_size=[g.nodes[n].get("size", 30) for n in g.nodes()],
        alpha=0.85,
        node_color="#5fa55a",
    )
    nx.draw_networkx_edges(
        g,
        pos,
        width=[g.edges[e].get("w", 0.4) for e in g.edges()],
        arrows=False,
        alpha=0.35,
    )
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path
