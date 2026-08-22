from __future__ import annotations

import json
import math
import subprocess
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

from automaton_invariants import compare_invariants, compute_automaton_invariants, save_invariants
from preimage_automaton import build_preimage_automaton
from reverse_graph_builder import resolve_root


class DepthMemoryError(RuntimeError):
    def __init__(self, root: str | int, depth: int, message: str) -> None:
        super().__init__(message)
        self.root = root
        self.depth = depth


def _linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    n = len(xs)
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0
    return (n * sxy - sx * sy) / den


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _max(values: list[float]) -> float:
    return max(values) if values else 0.0


def _depth_schedule(depth_min: int, depth_max: int, step: int) -> list[int]:
    if step <= 0:
        raise ValueError("step must be > 0")
    if depth_max < depth_min:
        raise ValueError("depth_max must be >= depth_min")
    return list(range(depth_min, depth_max + 1, step))


def _cache_dir(output_dir: Path) -> Path:
    d = output_dir / "cache" / "convergence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _inv_cache_path(
    output_dir: Path,
    root_label: str,
    depth: int,
    max_bits: int | None,
    a_max: int,
) -> Path:
    mb = "none" if max_bits is None else str(int(max_bits))
    return _cache_dir(output_dir) / f"invariants_{root_label}_d{depth}_b{mb}_a{int(a_max)}.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_invariants_cached(
    root: str | int,
    depth: int,
    max_bits: int | None,
    a_max: int,
    output_dir: Path,
    minimize: bool = True,
    memory_safe: bool = False,
) -> dict[str, Any]:
    root_label, _ = resolve_root(root)
    inv_path = _inv_cache_path(output_dir, root_label, depth, max_bits, a_max)
    if inv_path.exists():
        return _load_json(inv_path)

    if memory_safe:
        worker_path = Path(__file__).resolve().parent / "invariant_worker.py"
        cmd = [
            sys.executable,
            str(worker_path),
            "--root",
            str(root),
            "--depth",
            str(int(depth)),
            "--a-max",
            str(int(a_max)),
            "--output",
            str(inv_path),
        ]
        if max_bits is not None:
            cmd.extend(["--max-bits", str(int(max_bits))])
        cmd.append("--minimize" if minimize else "--no-minimize")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            combined = f"{proc.stdout}\n{proc.stderr}".lower()
            if "memoryerror" in combined:
                raise DepthMemoryError(
                    root=root,
                    depth=depth,
                    message=(
                        f"MemoryError while computing invariants for root={root} depth={depth}. "
                        "Try lower depth-max and/or max-bits."
                    ),
                )
            raise RuntimeError(
                "Worker failed for root="
                f"{root} depth={depth} (code={proc.returncode}). "
                f"stderr tail: {proc.stderr[-800:] if proc.stderr else ''}"
            )
        return _load_json(inv_path)

    bundle = build_preimage_automaton(
        root=root,
        max_depth=depth,
        max_bits=max_bits,
        a_max=a_max,
        minimize=minimize,
        include_forward_summary=False,
    )
    inv = compute_automaton_invariants(bundle)
    save_invariants(inv, inv_path)
    return inv


def _series_from_invariants(depths: list[int], invs: list[dict[str, Any]]) -> dict[str, list[float]]:
    return {
        "depths": depths,
        "mean_growth_ratio": [float(inv["growth"]["mean"]) for inv in invs],
        "mean_entropy": [float(inv["entropy"]["mean_entropy"]) for inv in invs],
        "signature_entropy": [float(inv["signatures"]["signature_entropy"]) for inv in invs],
        "width_max": [float(inv["width"]["max_width"]) for inv in invs],
    }


def _deltas(values: list[float]) -> list[float]:
    if len(values) < 2:
        return []
    return [abs(values[i] - values[i - 1]) for i in range(1, len(values))]


def _convergence_block(depths: list[int], values: list[float]) -> dict[str, Any]:
    deltas = _deltas(values)
    slope = _linear_slope([float(d) for d in depths], values) if len(values) >= 2 else 0.0
    mean_delta = _mean(deltas)
    return {
        "values": values,
        "deltas": deltas,
        "mean_delta": mean_delta,
        "max_delta": _max(deltas),
        "stability": 1.0 / (1.0 + mean_delta),
        "slope": slope,
    }


def analyze_convergence(
    root: str | int,
    depth_max: int,
    step: int = 2,
    depth_min: int = 4,
    max_bits: int | None = None,
    a_max: int = 8,
    output_dir: str | Path = "output",
    minimize: bool = True,
    memory_safe: bool = False,
    allow_partial: bool = False,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    depths = _depth_schedule(depth_min=depth_min, depth_max=depth_max, step=step)
    invs: list[dict[str, Any]] = []
    actual_depths: list[int] = []
    stop_reason: str | None = None
    root_label, _ = resolve_root(root)
    for d in depths:
        print(
            f"[convergence] root={root_label} depth={d} "
            f"(memory_safe={'on' if memory_safe else 'off'})"
        )
        try:
            inv = _build_invariants_cached(
                root=root,
                depth=d,
                max_bits=max_bits,
                a_max=a_max,
                output_dir=out_dir,
                minimize=minimize,
                memory_safe=memory_safe,
            )
            invs.append(inv)
            actual_depths.append(d)
        except DepthMemoryError as exc:
            if allow_partial and invs:
                stop_reason = (
                    f"partial_by_oom_at_depth_{int(exc.depth)}"
                )
                print(
                    f"[convergence] OOM at depth={exc.depth}, "
                    "returning partial series from successful depths."
                )
                break
            raise

    if not invs:
        raise RuntimeError(
            f"Convergence failed for root={root_label}: no successful depth points. "
            "Decrease --depth-max and/or --max-bits, or use --allow-partial with lower start."
        )

    series = _series_from_invariants(actual_depths, invs)

    conv_growth = _convergence_block(depths, series["mean_growth_ratio"])
    conv_entropy = _convergence_block(depths, series["mean_entropy"])
    conv_sig = _convergence_block(depths, series["signature_entropy"])
    conv_width = _convergence_block(depths, series["width_max"])

    final_inv = invs[-1] if invs else {}

    return {
        "root": root_label,
        "depths": actual_depths,
        "requested_depths": depths,
        "truncated": bool(stop_reason is not None),
        "stop_reason": stop_reason,
        "invariant_series": series,
        "invariants": {
            "growth": conv_growth,
            "entropy": conv_entropy,
            "signature_entropy": conv_sig,
            "width_max": conv_width,
        },
        "deltas": {
            "mean_growth_ratio": conv_growth["deltas"],
            "mean_entropy": conv_entropy["deltas"],
            "signature_entropy": conv_sig["deltas"],
            "width_max": conv_width["deltas"],
        },
        "stability": {
            "growth": conv_growth["stability"],
            "entropy": conv_entropy["stability"],
            "signature_entropy": conv_sig["stability"],
            "width_max": conv_width["stability"],
        },
        "slopes": {
            "growth": conv_growth["slope"],
            "entropy": conv_entropy["slope"],
            "signature_entropy": conv_sig["slope"],
            "width_max": conv_width["slope"],
        },
        "final_invariants": final_inv,
    }


def save_convergence(data: dict[str, Any], output_dir: str | Path = "output") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"convergence_{data['root']}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _pair_key(a: str, b: str) -> str:
    return f"{a}|{b}"


def _cluster_roots(
    roots: list[str],
    pair_dist: dict[str, float],
    epsilon: float,
) -> dict[str, list[str]]:
    # Graph components by threshold distance
    adj: dict[str, set[str]] = {r: set() for r in roots}
    for i, r1 in enumerate(roots):
        for r2 in roots[i + 1 :]:
            d = pair_dist.get(_pair_key(r1, r2), pair_dist.get(_pair_key(r2, r1), math.inf))
            if d < epsilon:
                adj[r1].add(r2)
                adj[r2].add(r1)

    visited: set[str] = set()
    clusters: dict[str, list[str]] = {}
    cid = 1
    for root in roots:
        if root in visited:
            continue
        stack = [root]
        comp = []
        visited.add(root)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in adj[cur]:
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        clusters[f"cluster_{cid}"] = sorted(comp)
        cid += 1
    return clusters


def analyze_universality(
    roots: list[str | int],
    depth_max: int,
    step: int = 2,
    depth_min: int = 4,
    max_bits: int | None = None,
    a_max: int = 8,
    output_dir: str | Path = "output",
    minimize: bool = True,
    epsilon: float = 1.0,
    memory_safe: bool = False,
    allow_partial: bool = False,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conv_results = [
        analyze_convergence(
            root=root,
            depth_max=depth_max,
            step=step,
            depth_min=depth_min,
            max_bits=max_bits,
            a_max=a_max,
            output_dir=out_dir,
            minimize=minimize,
            memory_safe=memory_safe,
            allow_partial=allow_partial,
        )
        for root in roots
    ]

    root_labels = [str(res["root"]) for res in conv_results]
    final_inv_map = {str(res["root"]): res["final_invariants"] for res in conv_results}

    pairwise_distances: dict[str, float] = {}
    pairwise_similarity: dict[str, float] = {}
    distance_values: list[float] = []
    for r1, r2 in combinations(root_labels, 2):
        cmp_res = compare_invariants(final_inv_map[r1], final_inv_map[r2])
        k = _pair_key(r1, r2)
        pairwise_distances[k] = float(cmp_res["l2_distance"])
        pairwise_similarity[k] = float(cmp_res["similarity_score"])
        distance_values.append(float(cmp_res["l2_distance"]))

    mean_pairwise_distance = _mean(distance_values)
    universality_score = 1.0 / (1.0 + mean_pairwise_distance)
    clusters = _cluster_roots(root_labels, pairwise_distances, epsilon=epsilon)

    return {
        "roots": root_labels,
        "depths": conv_results[0]["depths"] if conv_results else [],
        "pairwise_distances": pairwise_distances,
        "pairwise_similarity": pairwise_similarity,
        "mean_pairwise_distance": mean_pairwise_distance,
        "universality_score": universality_score,
        "clusters": clusters,
        "convergence": {str(res["root"]): res for res in conv_results},
    }


def save_universality(data: dict[str, Any], output_dir: str | Path = "output") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "universality.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def plot_convergence(result: dict[str, Any], output_dir: str | Path = "output") -> list[Path]:
    import matplotlib.pyplot as plt

    out_dir = Path(output_dir) / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    root = str(result["root"])
    depths = list(result["depths"])
    series = result["invariant_series"]

    artifacts: list[Path] = []

    # Invariant vs depth
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    items = [
        ("mean_growth_ratio", "Mean Growth Ratio"),
        ("mean_entropy", "Mean Entropy"),
        ("signature_entropy", "Signature Entropy"),
        ("width_max", "Max Width"),
    ]
    for i, (key, title) in enumerate(items):
        r = i // 2
        c = i % 2
        ax[r][c].plot(depths, series[key], marker="o")
        ax[r][c].set_title(title)
        ax[r][c].set_xlabel("depth")
        ax[r][c].grid(True, alpha=0.3)
    fig.suptitle(f"Convergence Series: {root}")
    p1 = out_dir / f"convergence_series_{root}.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=180)
    plt.close(fig)
    artifacts.append(p1)

    # Delta vs depth-step
    fig2, ax2 = plt.subplots(2, 2, figsize=(11, 8))
    delta_items = [
        ("mean_growth_ratio", "Delta Mean Growth"),
        ("mean_entropy", "Delta Mean Entropy"),
        ("signature_entropy", "Delta Signature Entropy"),
        ("width_max", "Delta Max Width"),
    ]
    ddepth = depths[1:] if len(depths) > 1 else []
    for i, (key, title) in enumerate(delta_items):
        r = i // 2
        c = i % 2
        vals = result["deltas"][key]
        ax2[r][c].plot(ddepth, vals, marker="o")
        ax2[r][c].set_title(title)
        ax2[r][c].set_xlabel("depth")
        ax2[r][c].grid(True, alpha=0.3)
    fig2.suptitle(f"Convergence Deltas: {root}")
    p2 = out_dir / f"convergence_deltas_{root}.png"
    fig2.tight_layout()
    fig2.savefig(p2, dpi=180)
    plt.close(fig2)
    artifacts.append(p2)

    return artifacts


def plot_universality(data: dict[str, Any], output_dir: str | Path = "output") -> list[Path]:
    import matplotlib.pyplot as plt

    out_dir = Path(output_dir) / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    roots = list(data["roots"])
    conv = data["convergence"]
    depths = data.get("depths", [])

    # Cross-root invariant comparison vs depth
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    inv_keys = [
        ("mean_growth_ratio", "Mean Growth Ratio"),
        ("mean_entropy", "Mean Entropy"),
        ("signature_entropy", "Signature Entropy"),
        ("width_max", "Max Width"),
    ]
    for i, (key, title) in enumerate(inv_keys):
        r = i // 2
        c = i % 2
        for root in roots:
            series = conv[root]["invariant_series"][key]
            ax[r][c].plot(depths, series, marker="o", label=root)
        ax[r][c].set_title(title)
        ax[r][c].set_xlabel("depth")
        ax[r][c].grid(True, alpha=0.3)
    ax[0][0].legend()
    fig.suptitle("Cross-root Invariant Comparison")
    p1 = out_dir / "universality_invariants.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=180)
    plt.close(fig)
    artifacts.append(p1)

    # Pairwise distance heatmap
    n = len(roots)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    for i, r1 in enumerate(roots):
        for j, r2 in enumerate(roots):
            if i == j:
                matrix[i][j] = 0.0
            else:
                k12 = _pair_key(r1, r2)
                k21 = _pair_key(r2, r1)
                matrix[i][j] = float(
                    data["pairwise_distances"].get(k12, data["pairwise_distances"].get(k21, 0.0))
                )

    fig2, ax2 = plt.subplots(figsize=(7, 6))
    im = ax2.imshow(matrix, cmap="YlOrRd")
    ax2.set_xticks(range(n), roots, rotation=30, ha="right")
    ax2.set_yticks(range(n), roots)
    for i in range(n):
        for j in range(n):
            ax2.text(j, i, f"{matrix[i][j]:.3f}", ha="center", va="center", fontsize=8)
    ax2.set_title("Pairwise Invariant Distances")
    fig2.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    p2 = out_dir / "universality_distances.png"
    fig2.tight_layout()
    fig2.savefig(p2, dpi=180)
    plt.close(fig2)
    artifacts.append(p2)

    return artifacts
