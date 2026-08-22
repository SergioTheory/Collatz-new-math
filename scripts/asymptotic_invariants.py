from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

import numpy as np
try:
    from scipy.optimize import curve_fit
except Exception:  # pragma: no cover - optional dependency guard
    curve_fit = None

from automaton_convergence import analyze_convergence
from reverse_graph_builder import resolve_root

InvariantSeries = dict[str, list[float] | list[int]]

INVARIANT_KEYS: dict[str, tuple[str, str]] = {
    "mean_growth_ratio": ("growth", "asymptotic_growth.png"),
    "mean_entropy": ("entropy", "asymptotic_entropy.png"),
    "signature_entropy": ("signature", "asymptotic_signature.png"),
    "width_max": ("width", "asymptotic_width.png"),
}


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return 0.0
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return 0.0
    sse = float(np.sum((y_true - y_pred) ** 2))
    sst = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    if sst <= 0:
        return 1.0 if sse <= 1e-15 else 0.0
    return float(1.0 - (sse / sst))


def _exp_model(d: np.ndarray, L: float, A: float, k: float) -> np.ndarray:
    return L + A * np.exp(-k * d)


def _power_model(d: np.ndarray, L: float, A: float, k: float) -> np.ndarray:
    return L + A / np.power(d, k)


def _linear_model(d: np.ndarray, L: float, A: float) -> np.ndarray:
    # Контрольная модель, где L - интерсепт, A - наклон.
    return L + A * d


def _extract_ci95(cov: np.ndarray | None, idx: int) -> list[float] | None:
    if cov is None:
        return None
    if cov.ndim != 2 or idx < 0 or idx >= cov.shape[0]:
        return None
    var = float(cov[idx, idx])
    if not math.isfinite(var) or var < 0:
        return None
    sigma = math.sqrt(var)
    return [float(-1.96 * sigma), float(1.96 * sigma)]


def _safe_curve_fit(
    model: Callable[..., np.ndarray],
    x: np.ndarray,
    y: np.ndarray,
    p0: list[float],
    bounds: tuple[list[float], list[float]],
) -> tuple[np.ndarray, np.ndarray | None] | None:
    if curve_fit is None:
        raise RuntimeError(
            "scipy is required for asymptotic fitting. Install dependencies from requirements.txt"
        )
    try:
        params, cov = curve_fit(
            model,
            x,
            y,
            p0=p0,
            bounds=bounds,
            maxfev=50_000,
        )
        return params, cov
    except Exception:
        return None


def _fit_models(depths: list[int], values: list[float], tail_threshold: float) -> dict[str, Any]:
    x = np.asarray(depths, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.size < 2:
        return {
            "models": {},
            "best_model": None,
            "best_fit": None,
            "extrapolation_depth_20": None,
        }

    y_last = float(y[-1])
    y_first = float(y[0])
    y_span = float(y_first - y_last)

    models: dict[str, dict[str, Any]] = {}

    exp_fit = _safe_curve_fit(
        _exp_model,
        x,
        y,
        p0=[y_last, y_span, 0.25],
        bounds=([-np.inf, -np.inf, 0.0], [np.inf, np.inf, np.inf]),
    )
    if exp_fit is not None:
        p, cov = exp_fit
        pred = _exp_model(x, *p)
        rmse = _rmse(y, pred)
        slope_last = float((y[-1] - y[-2]) / (x[-1] - x[-2])) if x.size >= 2 else 0.0
        tail = values[-3:] if len(values) >= 3 else values[:]
        max_delta_tail = (
            max(abs(tail[i] - tail[i - 1]) for i in range(1, len(tail))) if len(tail) >= 2 else 0.0
        )
        max_delta_tail_norm = max_delta_tail / max(1.0, abs(float(tail[-1]))) if tail else 0.0
        models["exp"] = {
            "params": {"L": float(p[0]), "A": float(p[1]), "k": float(p[2])},
            "rmse": rmse,
            "r2": _r2(y, pred),
            "limit_estimate": float(p[0]),
            "limit_ci95_delta": _extract_ci95(cov, 0),
            "convergence_score": float(1.0 / (1.0 + rmse + abs(slope_last))),
            "slope_last": slope_last,
            "max_delta_tail": max_delta_tail,
            "max_delta_tail_norm": max_delta_tail_norm,
            "tail_stable": bool(max_delta_tail_norm < tail_threshold),
            "converged": bool((max_delta_tail_norm < tail_threshold) and (abs(slope_last) < tail_threshold)),
            "prediction_depth_20": float(_exp_model(np.asarray([20.0]), *p)[0]),
        }

    power_fit = _safe_curve_fit(
        _power_model,
        x,
        y,
        p0=[y_last, y_span * max(1.0, x[0]), 1.0],
        bounds=([-np.inf, -np.inf, 0.0], [np.inf, np.inf, np.inf]),
    )
    if power_fit is not None:
        p, cov = power_fit
        pred = _power_model(x, *p)
        rmse = _rmse(y, pred)
        slope_last = float((y[-1] - y[-2]) / (x[-1] - x[-2])) if x.size >= 2 else 0.0
        tail = values[-3:] if len(values) >= 3 else values[:]
        max_delta_tail = (
            max(abs(tail[i] - tail[i - 1]) for i in range(1, len(tail))) if len(tail) >= 2 else 0.0
        )
        max_delta_tail_norm = max_delta_tail / max(1.0, abs(float(tail[-1]))) if tail else 0.0
        models["power"] = {
            "params": {"L": float(p[0]), "A": float(p[1]), "k": float(p[2])},
            "rmse": rmse,
            "r2": _r2(y, pred),
            "limit_estimate": float(p[0]),
            "limit_ci95_delta": _extract_ci95(cov, 0),
            "convergence_score": float(1.0 / (1.0 + rmse + abs(slope_last))),
            "slope_last": slope_last,
            "max_delta_tail": max_delta_tail,
            "max_delta_tail_norm": max_delta_tail_norm,
            "tail_stable": bool(max_delta_tail_norm < tail_threshold),
            "converged": bool((max_delta_tail_norm < tail_threshold) and (abs(slope_last) < tail_threshold)),
            "prediction_depth_20": float(_power_model(np.asarray([20.0]), *p)[0]),
        }

    linear_fit = _safe_curve_fit(
        _linear_model,
        x,
        y,
        p0=[y_last, (y[-1] - y[0]) / max(1.0, (x[-1] - x[0]))],
        bounds=([-np.inf, -np.inf], [np.inf, np.inf]),
    )
    if linear_fit is not None:
        p, cov = linear_fit
        pred = _linear_model(x, *p)
        rmse = _rmse(y, pred)
        slope_last = float((y[-1] - y[-2]) / (x[-1] - x[-2])) if x.size >= 2 else 0.0
        tail = values[-3:] if len(values) >= 3 else values[:]
        max_delta_tail = (
            max(abs(tail[i] - tail[i - 1]) for i in range(1, len(tail))) if len(tail) >= 2 else 0.0
        )
        max_delta_tail_norm = max_delta_tail / max(1.0, abs(float(tail[-1]))) if tail else 0.0
        models["linear"] = {
            "params": {"L": float(p[0]), "A": float(p[1])},
            "rmse": rmse,
            "r2": _r2(y, pred),
            "limit_estimate": float(p[0]),
            "limit_ci95_delta": _extract_ci95(cov, 0),
            "limit_is_asymptotic": bool(abs(float(p[1])) < 1e-6),
            "convergence_score": float(1.0 / (1.0 + rmse + abs(slope_last))),
            "slope_last": slope_last,
            "max_delta_tail": max_delta_tail,
            "max_delta_tail_norm": max_delta_tail_norm,
            "tail_stable": bool(max_delta_tail_norm < tail_threshold),
            "converged": bool((max_delta_tail_norm < tail_threshold) and (abs(slope_last) < tail_threshold)),
            "prediction_depth_20": float(_linear_model(np.asarray([20.0]), *p)[0]),
        }

    if not models:
        return {
            "models": {},
            "best_model": None,
            "best_fit": None,
            "extrapolation_depth_20": None,
        }

    best_model = min(models.items(), key=lambda kv: float(kv[1]["rmse"]))[0]
    best_fit = models[best_model]

    return {
        "models": models,
        "best_model": best_model,
        "best_fit": best_fit,
        "extrapolation_depth_20": best_fit.get("prediction_depth_20"),
    }


def analyze_asymptotic_root(
    root: str | int,
    depth_min: int = 4,
    depth_max: int = 16,
    step: int = 2,
    max_bits: int | None = 120,
    a_max: int = 8,
    output_dir: str | Path = "output",
    minimize: bool = True,
    tail_threshold: float = 0.05,
    memory_safe: bool = False,
    allow_partial: bool = False,
) -> dict[str, Any]:
    conv = analyze_convergence(
        root=root,
        depth_max=depth_max,
        step=step,
        depth_min=depth_min,
        max_bits=max_bits,
        a_max=a_max,
        output_dir=output_dir,
        minimize=minimize,
        memory_safe=memory_safe,
        allow_partial=allow_partial,
    )
    root_label, _ = resolve_root(root)
    series: InvariantSeries = conv["invariant_series"]
    depths = [int(d) for d in series["depths"]]

    fits: dict[str, Any] = {}
    limit_estimates: dict[str, float | None] = {}
    for invariant in INVARIANT_KEYS.keys():
        values = [float(v) for v in series[invariant]]
        fit = _fit_models(depths, values, tail_threshold=tail_threshold)
        fits[invariant] = {
            "values": values,
            **fit,
        }
        best_fit = fit.get("best_fit") or {}
        limit_estimates[invariant] = (
            float(best_fit["limit_estimate"]) if "limit_estimate" in best_fit else None
        )

    return {
        "root": root_label,
        "depths": depths,
        "requested_depths": list(conv.get("requested_depths", depths)),
        "truncated": bool(conv.get("truncated", False)),
        "stop_reason": conv.get("stop_reason"),
        "params": {
            "depth_min": int(depth_min),
            "depth_max": int(depth_max),
            "step": int(step),
            "max_bits": int(max_bits) if max_bits is not None else None,
            "a_max": int(a_max),
            "tail_threshold": float(tail_threshold),
            "minimize": bool(minimize),
            "memory_safe": bool(memory_safe),
            "allow_partial": bool(allow_partial),
        },
        "invariant_series": {
            k: [float(v) for v in series[k]]
            for k in ("mean_growth_ratio", "mean_entropy", "signature_entropy", "width_max")
        },
        "fits": fits,
        "limit_estimates": limit_estimates,
    }


def save_asymptotic_root(result: dict[str, Any], output_dir: str | Path = "output") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"asymptotic_{result['root']}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _pair_key(left: str, right: str) -> str:
    return f"{left}|{right}"


def _relative_diff(a: float, b: float) -> float:
    denom = (abs(a) + abs(b)) / 2.0
    if denom <= 1e-15:
        return 0.0
    return abs(a - b) / denom


def compare_asymptotic_limits(root_results: list[dict[str, Any]]) -> dict[str, Any]:
    roots = [str(r["root"]) for r in root_results]
    by_root = {str(r["root"]): r for r in root_results}

    pairwise: dict[str, Any] = {}
    for left, right in combinations(roots, 2):
        block: dict[str, Any] = {}
        for invariant in INVARIANT_KEYS.keys():
            lfit = by_root[left]["fits"][invariant]
            rfit = by_root[right]["fits"][invariant]
            lb = lfit.get("best_fit") or {}
            rb = rfit.get("best_fit") or {}
            if "limit_estimate" not in lb or "limit_estimate" not in rb:
                block[invariant] = None
                continue
            l_limit = float(lb["limit_estimate"])
            r_limit = float(rb["limit_estimate"])
            block[invariant] = {
                "limit_distance": abs(l_limit - r_limit),
                "relative_error": _relative_diff(l_limit, r_limit),
                "left_model": lfit.get("best_model"),
                "right_model": rfit.get("best_model"),
                "left_rmse": float(lb.get("rmse", 0.0)),
                "right_rmse": float(rb.get("rmse", 0.0)),
                "left_converged": bool(lb.get("converged", False)),
                "right_converged": bool(rb.get("converged", False)),
            }
        pairwise[_pair_key(left, right)] = block

    x27_summary: list[dict[str, Any]] = []
    if "xstar" in by_root and "27" in by_root:
        lroot = by_root["xstar"]
        rroot = by_root["27"]
        for invariant in INVARIANT_KEYS.keys():
            lfit = lroot["fits"][invariant]
            rfit = rroot["fits"][invariant]
            lb = lfit.get("best_fit") or {}
            rb = rfit.get("best_fit") or {}
            if "limit_estimate" not in lb or "limit_estimate" not in rb:
                continue
            l_limit = float(lb["limit_estimate"])
            r_limit = float(rb["limit_estimate"])
            x27_summary.append(
                {
                    "invariant": invariant,
                    "limit_xstar": l_limit,
                    "limit_27": r_limit,
                    "relative_diff": _relative_diff(l_limit, r_limit),
                    "converged": bool(lb.get("converged", False) and rb.get("converged", False)),
                    "model_xstar": lfit.get("best_model"),
                    "model_27": rfit.get("best_model"),
                    "rmse_xstar": float(lb.get("rmse", 0.0)),
                    "rmse_27": float(rb.get("rmse", 0.0)),
                }
            )

    return {
        "roots": roots,
        "pairwise_limits": pairwise,
        "xstar_vs_27": x27_summary,
    }


def save_asymptotic_compare(data: dict[str, Any], output_dir: str | Path = "output") -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "asymptotic_compare.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def analyze_asymptotic(
    roots: list[str | int],
    depth_min: int = 4,
    depth_max: int = 16,
    step: int = 2,
    max_bits: int | None = 120,
    a_max: int = 8,
    output_dir: str | Path = "output",
    minimize: bool = True,
    tail_threshold: float = 0.05,
    memory_safe: bool = False,
    allow_partial: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root_results = [
        analyze_asymptotic_root(
            root=root,
            depth_min=depth_min,
            depth_max=depth_max,
            step=step,
            max_bits=max_bits,
            a_max=a_max,
            output_dir=output_dir,
            minimize=minimize,
            tail_threshold=tail_threshold,
            memory_safe=memory_safe,
            allow_partial=allow_partial,
        )
        for root in roots
    ]
    compare = compare_asymptotic_limits(root_results)
    return root_results, compare


def _predict_curve(
    model_name: str,
    params: dict[str, float],
    x: np.ndarray,
) -> np.ndarray:
    if model_name == "exp":
        return _exp_model(x, float(params["L"]), float(params["A"]), float(params["k"]))
    if model_name == "power":
        return _power_model(x, float(params["L"]), float(params["A"]), float(params["k"]))
    return _linear_model(x, float(params["L"]), float(params["A"]))


def plot_asymptotic(
    root_results: list[dict[str, Any]],
    output_dir: str | Path = "output",
) -> list[Path]:
    import matplotlib.pyplot as plt

    out = Path(output_dir) / "plots"
    out.mkdir(parents=True, exist_ok=True)

    artifacts: list[Path] = []
    for invariant, (short_name, file_name) in INVARIANT_KEYS.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        for result in root_results:
            root = str(result["root"])
            depths = np.asarray(result["depths"], dtype=float)
            values = np.asarray(result["invariant_series"][invariant], dtype=float)
            ax.scatter(depths, values, s=36, label=f"{root}: points")

            fit_block = result["fits"][invariant]
            best_model = fit_block.get("best_model")
            best_fit = fit_block.get("best_fit") or {}
            params = best_fit.get("params")
            if best_model and params:
                x_line = np.linspace(depths.min(), max(depths.max(), 20.0), 200)
                y_line = _predict_curve(best_model, params, x_line)
                ax.plot(x_line, y_line, linewidth=1.8, label=f"{root}: fit ({best_model})")
                if "limit_estimate" in best_fit:
                    limit_val = float(best_fit["limit_estimate"])
                    ax.axhline(limit_val, linestyle="--", linewidth=1.0, alpha=0.7)

        ax.set_title(f"Asymptotic fit: {short_name}")
        ax.set_xlabel("Depth")
        ax.set_ylabel(invariant)
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)

        path = out / file_name
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        artifacts.append(path)

    return artifacts
