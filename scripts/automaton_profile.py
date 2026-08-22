from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automaton_compare import compute_metrics
from graph_export import (
    plot_layered_dag_colored,
    plot_multi_branch_growth,
    plot_series_by_depth,
    plot_shift_histogram,
    plot_signature_overlap_matrix,
)


def build_profile(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics = compute_metrics(bundle)
    profile = {
        "root_label": metrics["root_label"],
        "root_value": metrics["root_value"],
        "node_count": metrics["node_count"],
        "edge_count": metrics["edge_count"],
        "max_depth": metrics["max_depth"],
        "unique_signatures": metrics["unique_signatures"],
        "nodes_by_depth": metrics["nodes_by_depth"],
        "cumulative_nodes_by_depth": metrics["cumulative_nodes_by_depth"],
        "unique_signatures_by_depth": metrics["unique_signatures_by_depth"],
        "entropy_by_depth": metrics["entropy_by_depth"],
        "outdegree_distribution": metrics["outdegree_distribution"],
        "shift_distribution": metrics["shift_distribution"],
        "branch_growth_slope": metrics["branch_growth_slope"],
        "confluence": metrics["confluence"],
    }
    return profile


def save_profile(profile: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def render_profile_plots(
    bundle: dict[str, Any],
    profile: dict[str, Any],
    output_dir: str | Path,
) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    root_label = profile["root_label"]

    node_to_sig = bundle.get("signatures", {}).get("node_signatures", {})
    artifacts = [
        plot_layered_dag_colored(
            bundle["graph"],
            out / f"layered_depth_{root_label}.png",
            f"Layered DAG by Depth: {root_label}",
            color_by="depth",
        ),
        plot_layered_dag_colored(
            bundle["graph"],
            out / f"layered_signature_{root_label}.png",
            f"Layered DAG by Signature Class: {root_label}",
            color_by="signature",
            node_to_signature=node_to_sig,
        ),
        plot_series_by_depth(
            profile["nodes_by_depth"],
            out / f"branch_growth_{root_label}.png",
            f"Branch Growth N(depth): {root_label}",
            y_label="nodes",
        ),
        plot_series_by_depth(
            profile["cumulative_nodes_by_depth"],
            out / f"branch_growth_cumulative_{root_label}.png",
            f"Cumulative Branch Growth: {root_label}",
            y_label="cumulative nodes",
        ),
        plot_series_by_depth(
            profile["entropy_by_depth"],
            out / f"entropy_{root_label}.png",
            f"Entropy by Depth: {root_label}",
            y_label="entropy",
        ),
        plot_shift_histogram(
            bundle["graph"],
            out / f"shift_hist_profile_{root_label}.png",
            f"Shift Labels: {root_label}",
        ),
    ]
    return artifacts


def render_cross_profiles(
    metrics_list: list[dict[str, Any]],
    output_dir: str | Path,
) -> list[Path]:
    if len(metrics_list) < 2:
        return []
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return [
        plot_signature_overlap_matrix(
            metrics_list,
            out / "signature_overlap_matrix.png",
            "Canonical Signature Overlap",
        ),
        plot_multi_branch_growth(
            metrics_list,
            out / "compare_xstar_27_barina_branch_growth.png",
            "Branch Growth: xstar vs 27 vs barina",
        ),
    ]

