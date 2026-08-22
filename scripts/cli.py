from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from automaton_compare import compare_automata, compute_metrics, save_comparison
from automaton_convergence import (
    analyze_convergence,
    analyze_universality,
    plot_convergence,
    plot_universality,
    save_convergence,
    save_universality,
)
from automaton_diff_analyzer import analyze_automata_diff, save_diff_analysis
from asymptotic_invariants import (
    analyze_asymptotic,
    plot_asymptotic,
    save_asymptotic_compare,
    save_asymptotic_root,
)
from automaton_invariants import compute_automaton_invariants, save_invariants
from automaton_profile import (
    build_profile,
    render_cross_profiles,
    render_profile_plots,
    save_profile,
)
from automaton_search import run_candidate_search
from graph_export import (
    export_gexf,
    export_graph_csv,
    export_graphml,
    export_json,
    plot_comparison,
    plot_depth_heatmap,
    plot_layered_dag,
    plot_shift_histogram,
    plot_signature_tree,
)
from preimage_automaton import build_preimage_automaton, load_automaton, save_automaton
from reverse_graph_builder import resolve_root


def _max_bits_or_default(root_value: int, max_bits: int | None) -> int:
    if max_bits is not None:
        return int(max_bits)
    return int(root_value.bit_length() + 45)


def _bundle_path(output_dir: Path, root_label: str) -> Path:
    return output_dir / f"automaton_{root_label}.json"


def _graph_path(output_dir: Path, root_label: str) -> Path:
    return output_dir / f"reverse_graph_{root_label}.json"


def _profile_path(output_dir: Path, root_label: str) -> Path:
    return output_dir / f"profile_{root_label}.json"


def _invariants_path(output_dir: Path, root_label: str) -> Path:
    return output_dir / f"invariants_{root_label}.json"


def _upsert_summary_csv(rows: list[dict[str, Any]], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    merged: dict[str, dict[str, Any]] = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                merged[row["root_label"]] = row

    for row in rows:
        merged[str(row["root_label"])] = row

    fields = [
        "root_label",
        "root_value",
        "node_count",
        "edge_count",
        "unique_signatures",
        "max_depth",
        "branch_growth_slope",
        "merge_ratio",
        "max_indegree",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key in sorted(merged.keys()):
            row = merged[key]
            writer.writerow({field: row.get(field) for field in fields})


def _metric_row(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "root_label": metrics["root_label"],
        "root_value": metrics["root_value"],
        "node_count": metrics["node_count"],
        "edge_count": metrics["edge_count"],
        "unique_signatures": metrics["unique_signatures"],
        "max_depth": metrics["max_depth"],
        "branch_growth_slope": metrics["branch_growth_slope"],
        "merge_ratio": metrics["confluence"]["merge_ratio"],
        "max_indegree": metrics["confluence"]["max_indegree"],
    }


def _build_and_persist(
    root: str | int,
    depth: int,
    max_bits: int | None,
    a_max: int,
    output_dir: Path,
    minimize: bool,
    plot: bool,
    include_forward_summary: bool = False,
) -> dict[str, Any]:
    root_label, root_value = resolve_root(root)
    max_bits_resolved = _max_bits_or_default(root_value, max_bits)
    bundle = build_preimage_automaton(
        root=root,
        max_depth=depth,
        max_bits=max_bits_resolved,
        a_max=a_max,
        minimize=minimize,
        include_forward_summary=include_forward_summary,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    save_automaton(bundle, _bundle_path(output_dir, root_label))
    export_json(bundle["graph"], _graph_path(output_dir, root_label))
    export_graph_csv(bundle["graph"], output_dir, f"reverse_graph_{root_label}")

    plots_dir = output_dir / "plots"
    if plot:
        plot_layered_dag(
            bundle["graph"],
            plots_dir / f"layered_{root_label}.png",
            f"Layered Reverse DAG: {root_label}",
        )
        plot_depth_heatmap(
            bundle["graph"],
            plots_dir / f"heatmap_{root_label}.png",
            f"Depth/Bit Heatmap: {root_label}",
        )
        plot_shift_histogram(
            bundle["graph"],
            plots_dir / f"shift_hist_{root_label}.png",
            f"Shift Labels: {root_label}",
        )
        if bundle["signatures"].get("minimized"):
            plot_signature_tree(
                bundle,
                plots_dir / f"signature_tree_{root_label}.png",
                f"Signature Tree: {root_label}",
            )

    return bundle


def _load_or_build(
    root: str | int,
    depth: int,
    max_bits: int | None,
    a_max: int,
    output_dir: Path,
    minimize: bool,
    plot: bool,
) -> dict[str, Any]:
    root_label, _ = resolve_root(root)
    p = _bundle_path(output_dir, root_label)
    if p.exists():
        return load_automaton(p)
    return _build_and_persist(
        root=root,
        depth=depth,
        max_bits=max_bits,
        a_max=a_max,
        output_dir=output_dir,
        minimize=minimize,
        plot=plot,
    )


def _load_known_profiles(output_dir: Path) -> list[dict[str, Any]]:
    metrics_list = []
    for root in ("xstar", "27", "barina"):
        p = _bundle_path(output_dir, root)
        if not p.exists():
            continue
        try:
            bundle = load_automaton(p)
            metrics_list.append(compute_metrics(bundle))
        except Exception:
            continue
    return metrics_list


def run_build(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    bundle = _build_and_persist(
        root=args.root,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
        include_forward_summary=args.forward_summary,
    )
    metrics = compute_metrics(bundle)
    _upsert_summary_csv([_metric_row(metrics)], out_dir / "automaton_summary.csv")
    print(f"Built reverse automaton for {bundle['root_label']}")
    print(f"Graph: {_graph_path(out_dir, bundle['root_label'])}")
    print(f"Bundle: {_bundle_path(out_dir, bundle['root_label'])}")
    return 0


def run_compare(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    left = _load_or_build(
        root=args.left,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
    )
    right = _load_or_build(
        root=args.right,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
    )

    comp = compare_automata(left, right, normalize_depth=args.normalize_depth)
    out_path = out_dir / f"compare_{left['root_label']}_vs_{right['root_label']}.json"
    save_comparison(comp, out_path)

    lm = comp["left"]
    rm = comp["right"]
    _upsert_summary_csv([_metric_row(lm), _metric_row(rm)], out_dir / "automaton_summary.csv")

    if args.plot:
        plot_comparison(
            lm,
            rm,
            out_dir / "plots" / f"compare_{left['root_label']}_vs_{right['root_label']}.png",
            f"Automata Compare: {left['root_label']} vs {right['root_label']}",
        )

    print(f"Comparison saved: {out_path}")
    print(
        "Verdict: "
        f"{comp['comparison']['verdict']} ({comp['comparison'].get('verdict_en', '')})"
    )
    print(
        "Common canonical signatures: "
        f"{comp['comparison']['common_canonical_signature_count']}"
    )
    return 0


def run_diff(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)

    # Mandatory aligned conditions for diff:
    # same depth, same max_bits, same a_max, normalize_depth=True
    _, left_value = resolve_root(args.left)
    _, right_value = resolve_root(args.right)
    aligned_max_bits = (
        int(args.max_bits)
        if args.max_bits is not None
        else max(left_value.bit_length(), right_value.bit_length()) + 45
    )

    left = _build_and_persist(
        root=args.left,
        depth=args.depth,
        max_bits=aligned_max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
        include_forward_summary=False,
    )
    right = _build_and_persist(
        root=args.right,
        depth=args.depth,
        max_bits=aligned_max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
        include_forward_summary=False,
    )

    diff = analyze_automata_diff(left, right, max_items=args.max_items, motif_radius=args.motif_radius)
    out_path = out_dir / f"diff_{left['root_label']}_vs_{right['root_label']}.json"
    save_diff_analysis(diff, out_path)

    summary = diff["summary"]
    print("SUMMARY")
    print(f"first_divergence_depth: {summary['first_divergence_depth']}")
    print(f"rule_overlap_ratio: {summary['rule_overlap_ratio']:.6f}")
    print(f"transition_overlap_ratio: {summary['transition_overlap_ratio']:.6f}")
    print(f"structural_similarity_score: {summary['structural_similarity_score']:.6f}")
    print(f"Diff saved: {out_path}")
    return 0


def run_export(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    bundle = _load_or_build(
        root=args.root,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=False,
    )
    root_label = bundle["root_label"]

    fmt = args.export_format.lower()
    if fmt == "json":
        p = export_json(bundle["graph"], out_dir / f"reverse_graph_{root_label}.json")
    elif fmt == "csv":
        p_nodes, p_edges = export_graph_csv(bundle["graph"], out_dir, f"reverse_graph_{root_label}")
        print(f"CSV nodes: {p_nodes}")
        print(f"CSV edges: {p_edges}")
        return 0
    elif fmt == "graphml":
        p = export_graphml(bundle["graph"], out_dir / f"reverse_graph_{root_label}.graphml")
    elif fmt == "gexf":
        p = export_gexf(bundle["graph"], out_dir / f"reverse_graph_{root_label}.gexf")
    elif fmt == "png":
        p = plot_layered_dag(
            bundle["graph"],
            out_dir / "plots" / f"layered_{root_label}.png",
            f"Layered Reverse DAG: {root_label}",
        )
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

    print(f"Exported: {p}")
    return 0


def run_profile(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    bundle = _load_or_build(
        root=args.root,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=args.plot,
    )
    profile = build_profile(bundle)
    path = save_profile(profile, _profile_path(out_dir, bundle["root_label"]))

    artifacts = []
    if args.plot:
        artifacts = render_profile_plots(bundle, profile, out_dir / "plots")
        cross = render_cross_profiles(_load_known_profiles(out_dir), out_dir / "plots")
        artifacts.extend(cross)

    print(f"Profile saved: {path}")
    print(f"Node count: {profile['node_count']}")
    print(f"Unique signatures: {profile['unique_signatures']}")
    print(f"Max depth: {profile['max_depth']}")
    if artifacts:
        print(f"Plot artifacts: {len(artifacts)} files in {out_dir / 'plots'}")
    return 0


def run_search(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    target = _load_or_build(
        root=args.target,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=True,
        plot=False,
    )

    result = run_candidate_search(
        target_bundle=target,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        limit=args.limit,
        similarity_threshold=args.similarity_threshold,
        graph_limit=args.graph_limit,
    )
    result["target_metrics"] = compute_metrics(target)

    out_path = out_dir / f"signature_candidates_{target['root_label']}.json"
    export_json(result, out_path)
    print(f"Search saved: {out_path}")
    print(
        "Graph-class candidates: "
        f"{len(result['in_graph_same_signature_candidates'])}"
    )
    print(f"External exact signature hits: {len(result['same_signature_class'])}")
    print(
        "External scaled analogues (score >= "
        f"{args.similarity_threshold}): {len(result['scaled_analogues'])}"
    )
    return 0


def run_invariants(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    bundle = _build_and_persist(
        root=args.root,
        depth=args.depth,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        plot=False,
        include_forward_summary=False,
    )
    invariants = compute_automaton_invariants(bundle)
    out_path = save_invariants(invariants, _invariants_path(out_dir, bundle["root_label"]))

    print("INVARIANTS SUMMARY")
    print(f"mean_growth_ratio: {invariants['growth']['mean']:.6f}")
    print(f"mean_entropy: {invariants['entropy']['mean_entropy']:.6f}")
    print(f"signature_entropy: {invariants['signatures']['signature_entropy']:.6f}")
    print(f"mean_overlap: {invariants['stability']['mean_overlap']:.6f}")
    print(f"Saved: {out_path}")
    return 0


def run_convergence(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    result = analyze_convergence(
        root=args.root,
        depth_max=args.depth_max,
        step=args.step,
        depth_min=args.depth_min,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        memory_safe=args.memory_safe,
        allow_partial=args.allow_partial,
    )
    out_path = save_convergence(result, output_dir=out_dir)

    if args.plot:
        plot_convergence(result, output_dir=out_dir)

    print(f"CONVERGENCE SUMMARY ({result['root']})")
    mg = result["invariants"]["growth"]["mean_delta"]
    me = result["invariants"]["entropy"]["mean_delta"]
    ms = result["invariants"]["signature_entropy"]["mean_delta"]
    print(f"mean_growth -> {'stable' if mg < args.stable_threshold else 'drift'} (Δ={mg:.6f})")
    print(f"entropy -> {'stable' if me < args.stable_threshold else 'drift'} (Δ={me:.6f})")
    print(f"signature_entropy -> {'stable' if ms < args.stable_threshold else 'drift'} (Δ={ms:.6f})")
    print(f"Saved: {out_path}")
    return 0


def run_universality(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    result = analyze_universality(
        roots=args.roots,
        depth_max=args.depth_max,
        step=args.step,
        depth_min=args.depth_min,
        max_bits=args.max_bits,
        a_max=args.a_max,
        output_dir=out_dir,
        minimize=args.minimize,
        epsilon=args.epsilon,
        memory_safe=args.memory_safe,
        allow_partial=args.allow_partial,
    )
    out_path = save_universality(result, output_dir=out_dir)

    if args.plot:
        plot_universality(result, output_dir=out_dir)

    print("UNIVERSALITY SUMMARY")
    for k, v in sorted(result["pairwise_distances"].items()):
        roots = k.split("|")
        print(f"{roots[0]} vs {roots[1]} -> distance={float(v):.6f}")
    print(f"universality_score={float(result['universality_score']):.6f}")
    print(f"Saved: {out_path}")
    return 0


def run_asymptotic(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    try:
        root_results, compare_data = analyze_asymptotic(
            roots=args.roots,
            depth_min=args.depth_min,
            depth_max=args.depth_max,
            step=args.step,
            max_bits=args.max_bits,
            a_max=args.a_max,
            output_dir=out_dir,
            minimize=args.minimize,
            tail_threshold=args.tail_threshold,
            memory_safe=args.memory_safe,
            allow_partial=args.allow_partial,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 2

    saved_paths = [save_asymptotic_root(result, output_dir=out_dir) for result in root_results]
    compare_path = save_asymptotic_compare(compare_data, output_dir=out_dir)

    plot_artifacts = []
    if args.plot:
        plot_artifacts = plot_asymptotic(root_results, output_dir=out_dir)

    print("ASYMPTOTIC SUMMARY")
    for result in root_results:
        if bool(result.get("truncated")):
            print(
                f"{result['root']}: partial series "
                f"(reason={result.get('stop_reason')}, depths={result.get('depths')})"
            )
    for row in compare_data.get("xstar_vs_27", []):
        print(
            f"{row['invariant']}: "
            f"relative_diff={float(row['relative_diff']):.6f}, "
            f"models=({row['model_xstar']}, {row['model_27']}), "
            f"converged={bool(row['converged'])}"
        )

    for p in saved_paths:
        print(f"Saved: {p}")
    print(f"Saved: {compare_path}")
    if plot_artifacts:
        print(f"Plots: {len(plot_artifacts)} files in {out_dir / 'plots'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Preimage automata builder/comparator for Collatz Crystal Hunter2"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--depth", type=int, default=10)
        sp.add_argument("--max-bits", type=int, default=None)
        sp.add_argument("--a-max", type=int, default=8)
        sp.add_argument("--output-dir", default="output")
        sp.add_argument("--minimize", dest="minimize", action="store_true", default=True)
        sp.add_argument("--no-minimize", dest="minimize", action="store_false")
        sp.add_argument("--plot", dest="plot", action="store_true", default=True)
        sp.add_argument("--no-plot", dest="plot", action="store_false")
        sp.add_argument("--normalize-depth", dest="normalize_depth", action="store_true", default=True)
        sp.add_argument("--no-normalize-depth", dest="normalize_depth", action="store_false")

    p_build = sub.add_parser("build", help="build reverse graph + automaton")
    p_build.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    p_build.add_argument("--forward-summary", action="store_true", default=False)
    add_common(p_build)
    p_build.set_defaults(func=run_build)

    p_compare = sub.add_parser("compare", help="compare two automata")
    p_compare.add_argument("--left", required=True, help="xstar | 27 | barina | integer")
    p_compare.add_argument("--right", required=True, help="xstar | 27 | barina | integer")
    add_common(p_compare)
    p_compare.set_defaults(func=run_compare)

    p_diff = sub.add_parser(
        "diff",
        help="extract minimal structural differences between two automata",
    )
    p_diff.add_argument("--left", required=True, help="xstar | 27 | barina | integer")
    p_diff.add_argument("--right", required=True, help="xstar | 27 | barina | integer")
    p_diff.add_argument("--max-items", type=int, default=250, help="max listed items in diff output")
    p_diff.add_argument("--motif-radius", type=int, default=2, help="radius for local motif extraction")
    add_common(p_diff)
    p_diff.set_defaults(func=run_diff)

    p_export = sub.add_parser("export", help="export existing automaton graph")
    p_export.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    p_export.add_argument(
        "--export-format",
        default="json",
        choices=["json", "csv", "graphml", "gexf", "png"],
        help="json | csv | graphml | gexf | png",
    )
    add_common(p_export)
    p_export.set_defaults(func=run_export)

    p_profile = sub.add_parser("profile", help="build profile for one automaton")
    p_profile.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    add_common(p_profile)
    p_profile.set_defaults(func=run_profile)

    p_search = sub.add_parser("search", help="find in-graph and external candidates")
    p_search.add_argument("--target", required=True, help="xstar | 27 | barina | integer")
    p_search.add_argument("--limit", type=int, default=50, help="max external seeds to check")
    p_search.add_argument("--graph-limit", type=int, default=200, help="max in-graph candidates")
    p_search.add_argument("--similarity-threshold", type=float, default=0.72)
    add_common(p_search)
    p_search.set_defaults(func=run_search)

    p_inv = sub.add_parser("invariants", help="compute normalized automaton invariants")
    p_inv.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    add_common(p_inv)
    p_inv.set_defaults(func=run_invariants)

    p_conv = sub.add_parser("convergence", help="run depth-wise convergence analysis")
    p_conv.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    p_conv.add_argument("--depth-min", type=int, default=4)
    p_conv.add_argument("--depth-max", type=int, default=12)
    p_conv.add_argument("--step", type=int, default=2)
    p_conv.add_argument("--max-bits", type=int, default=None)
    p_conv.add_argument("--a-max", type=int, default=8)
    p_conv.add_argument("--output-dir", default="output")
    p_conv.add_argument("--minimize", dest="minimize", action="store_true", default=True)
    p_conv.add_argument("--no-minimize", dest="minimize", action="store_false")
    p_conv.add_argument("--plot", dest="plot", action="store_true", default=True)
    p_conv.add_argument("--no-plot", dest="plot", action="store_false")
    p_conv.add_argument("--memory-safe", dest="memory_safe", action="store_true", default=False)
    p_conv.add_argument("--no-memory-safe", dest="memory_safe", action="store_false")
    p_conv.add_argument("--allow-partial", dest="allow_partial", action="store_true", default=False)
    p_conv.add_argument("--no-allow-partial", dest="allow_partial", action="store_false")
    p_conv.add_argument("--stable-threshold", type=float, default=0.05)
    p_conv.set_defaults(func=run_convergence)

    p_uni = sub.add_parser("universality", help="run cross-root universality analysis")
    p_uni.add_argument("--roots", nargs="+", required=True, help="xstar 27 barina ...")
    p_uni.add_argument("--depth-min", type=int, default=4)
    p_uni.add_argument("--depth-max", type=int, default=12)
    p_uni.add_argument("--step", type=int, default=2)
    p_uni.add_argument("--max-bits", type=int, default=None)
    p_uni.add_argument("--a-max", type=int, default=8)
    p_uni.add_argument("--output-dir", default="output")
    p_uni.add_argument("--minimize", dest="minimize", action="store_true", default=True)
    p_uni.add_argument("--no-minimize", dest="minimize", action="store_false")
    p_uni.add_argument("--plot", dest="plot", action="store_true", default=True)
    p_uni.add_argument("--no-plot", dest="plot", action="store_false")
    p_uni.add_argument("--memory-safe", dest="memory_safe", action="store_true", default=False)
    p_uni.add_argument("--no-memory-safe", dest="memory_safe", action="store_false")
    p_uni.add_argument("--allow-partial", dest="allow_partial", action="store_true", default=False)
    p_uni.add_argument("--no-allow-partial", dest="allow_partial", action="store_false")
    p_uni.add_argument("--epsilon", type=float, default=1.0, help="cluster threshold by distance")
    p_uni.set_defaults(func=run_universality)

    p_asym = sub.add_parser("asymptotic", help="estimate asymptotic invariant limits")
    p_asym.add_argument("--roots", nargs="+", required=True, help="xstar 27 barina ...")
    p_asym.add_argument("--depth-min", type=int, default=4)
    p_asym.add_argument("--depth-max", type=int, default=16)
    p_asym.add_argument("--step", type=int, default=2)
    p_asym.add_argument("--max-bits", type=int, default=120)
    p_asym.add_argument("--a-max", type=int, default=8)
    p_asym.add_argument("--output-dir", default="output")
    p_asym.add_argument("--minimize", dest="minimize", action="store_true", default=True)
    p_asym.add_argument("--no-minimize", dest="minimize", action="store_false")
    p_asym.add_argument("--plot", dest="plot", action="store_true", default=True)
    p_asym.add_argument("--no-plot", dest="plot", action="store_false")
    p_asym.add_argument("--memory-safe", dest="memory_safe", action="store_true", default=False)
    p_asym.add_argument("--no-memory-safe", dest="memory_safe", action="store_false")
    p_asym.add_argument("--allow-partial", dest="allow_partial", action="store_true", default=True)
    p_asym.add_argument("--no-allow-partial", dest="allow_partial", action="store_false")
    p_asym.add_argument("--tail-threshold", type=float, default=0.05)
    p_asym.set_defaults(func=run_asymptotic)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
