#!/usr/bin/env python3
"""Multiprocess Front-C adversarial diagnostic (not a proof).

At a renewal point b_j=3, L_j=L_{j-1}+3 with
L_{j-1}~NB(2(j-1),1/2).  Thus Tao's phase contains
2^{-(L_j-1)}=2^{-(L_{j-1}+2)} modulo 3^n.

For large n the search covers low discrete-log frequencies xi=2^s, s=O(n),
plus deterministic random units.  Since 2 generates all units modulo 3^n,
"power of two" alone is not informative; a low exponent s=O(n) is.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

_TABLES = None
_EPSILONS = None


def nb_support(j: int, tail_tol: float = 1e-14) -> list[tuple[int, float]]:
    """Truncated normalized law of L_{j-1}; omitted mass <= tail_tol."""
    r = 2 * (j - 1)
    if r == 0:
        return [(0, 1.0)]
    out = []
    p = 2.0 ** (-r)
    total = 0.0
    l = r
    while True:
        out.append((l, p))
        total += p
        p *= 0.5 * l / (l - r + 1)
        l += 1
        if 1.0 - total <= tail_tol and l > r + 20:
            break
        if l > r + 100000:
            raise RuntimeError("NB truncation failed")
    return [(x, w / total) for x, w in out]


def build_tables(n: int) -> list[tuple[int, list[int], list[float]]]:
    """For each j store modulus 3^(n-2j+2), inverse powers, NB weights."""
    tables = []
    for j in range(1, n // 2 + 1):
        k = n - 2 * j + 2
        mod = 3 ** k
        inv2 = (mod + 1) // 2
        support = nb_support(j)
        residues = [pow(inv2, l_prev + 2, mod) for l_prev, _ in support]
        weights = [w for _, w in support]
        tables.append((mod, residues, weights))
    return tables


def init_worker(tables, epsilons):
    global _TABLES, _EPSILONS
    _TABLES = tables
    _EPSILONS = epsilons


def candidate_scores(xi: int) -> list[tuple[float, float, float]]:
    """Return (mean, min_j, max_j) black probability for every epsilon."""
    sums = [0.0] * len(_EPSILONS)
    mins = [1.0] * len(_EPSILONS)
    maxs = [0.0] * len(_EPSILONS)
    for mod, residues, weights in _TABLES:
        thresholds = [eps * mod for eps in _EPSILONS]
        ps = [0.0] * len(_EPSILONS)
        x = xi % mod
        for residue, weight in zip(residues, weights):
            r = (x * residue) % mod
            d = r if r <= mod - r else mod - r
            for q, threshold in enumerate(thresholds):
                if d <= threshold:
                    ps[q] += weight
        for q, p in enumerate(ps):
            sums[q] += p
            mins[q] = min(mins[q], p)
            maxs[q] = max(maxs[q], p)
    m = len(_TABLES)
    return [(s / m, lo, hi) for s, lo, hi in zip(sums, mins, maxs)]


def scan_chunk(chunk):
    """Candidate is (xi, low_s|None, kind). Return per-epsilon maxima."""
    best = [None] * len(_EPSILONS)
    best_low = [None] * len(_EPSILONS)
    best_random = [None] * len(_EPSILONS)
    for xi, low_s, kind in chunk:
        scores = candidate_scores(xi)
        for q, (avg, min_j, max_j) in enumerate(scores):
            rec = {"xi": xi, "low_s": low_s, "kind": kind,
                   "avg_black": avg, "min_black": min_j,
                   "max_black": max_j, "mean_white_prob": 1.0 - avg}
            if best[q] is None or avg > best[q]["avg_black"]:
                best[q] = rec
            if kind == "low_power" and (best_low[q] is None or avg > best_low[q]["avg_black"]):
                best_low[q] = rec
            if kind == "random_unit" and (best_random[q] is None or avg > best_random[q]["avg_black"]):
                best_random[q] = rec
    return best, best_low, best_random


def make_candidates(n: int, low_s_factor: float, random_count: int,
                    exhaustive_limit: int = 7):
    mod = 3 ** n
    if n <= exhaustive_limit:
        return [(xi, None, "exhaustive_unit") for xi in range(1, mod) if xi % 3], True
    candidates = []
    seen = set()
    low_s_max = max(200, int(math.ceil(low_s_factor * n)))
    for s in range(low_s_max):
        xi = pow(2, s, mod)
        if xi not in seen:
            candidates.append((xi, s, "low_power"))
            seen.add(xi)
    rng = random.Random(0xC011A7 + n)
    added = 0
    while added < random_count:
        xi = rng.randrange(1, mod)
        if xi % 3 and xi not in seen:
            candidates.append((xi, None, "random_unit"))
            seen.add(xi)
            added += 1
    return candidates, False


def theta_is_white(n: int, j: int, l_prev: int, xi: int, eps: float) -> bool:
    k = n - 2 * j + 2
    mod = 3 ** k
    inv2 = (mod + 1) // 2
    r = ((xi % mod) * pow(inv2, l_prev + 2, mod)) % mod
    d = min(r, mod - r)
    return d > eps * mod


def simulate_nwhite(n: int, xi: int, eps: float, paths: int, seed: int) -> dict:
    rng = random.Random(seed)
    values = []
    eta_cos = -math.log(math.cos(math.pi * eps))
    eta_eps3 = eps ** 3
    sum_cos = 0.0
    sum_eps3 = 0.0
    for _ in range(paths):
        L = 0
        white = 0
        for j in range(1, n // 2 + 1):
            b = 0
            for _ in range(2):
                a = 1
                while rng.random() < 0.5:
                    a += 1
                b += a
            L += b
            if b == 3 and theta_is_white(n, j, L - 3, xi, eps):
                white += 1
        values.append(white)
        sum_cos += math.exp(-eta_cos * white)
        sum_eps3 += math.exp(-eta_eps3 * white)
    values.sort()
    def quantile(q):
        return values[min(paths - 1, int(q * paths))]
    return {
        "paths": paths,
        "mean_Nwhite": sum(values) / paths,
        "q001": quantile(0.001), "q01": quantile(0.01), "q05": quantile(0.05),
        "zero_fraction": values.count(0) / paths,
        "eta_cos": eta_cos, "moment_eta_cos": sum_cos / paths,
        "eta_eps3": eta_eps3, "moment_eta_eps3": sum_eps3 / paths,
    }


def merge_max(parts, group: int, q: int):
    vals = [part[group][q] for part in parts if part[group][q] is not None]
    return max(vals, key=lambda r: r["avg_black"]) if vals else None


def e6_sstar(n: int):
    path = Path(__file__).resolve().parents[2] / "Collatz_NewMath" / "e6_results.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data.get("results", []):
        if row["n"] == n:
            return row["s*"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", nargs="+", type=int, default=[200, 400])
    ap.add_argument("--epsilons", nargs="+", type=float, default=[0.1, 0.05, 0.02, 0.01])
    ap.add_argument("--workers", type=int, default=min(30, os.cpu_count() or 1))
    ap.add_argument("--low-s-factor", type=float, default=4.0)
    ap.add_argument("--random-candidates", type=int, default=500)
    ap.add_argument("--mc-paths", type=int, default=30000)
    ap.add_argument("--out", default="front_c_large_results.json")
    args = ap.parse_args()

    output = []
    for n in args.ns:
        print(f"building exact NB/phase tables for n={n}", flush=True)
        tables = build_tables(n)
        candidates, exhaustive = make_candidates(n, args.low_s_factor, args.random_candidates)
        chunks = [candidates[i::args.workers] for i in range(args.workers)]
        print(f"scanning {len(candidates)} candidates with {args.workers} workers", flush=True)
        with ProcessPoolExecutor(max_workers=args.workers, initializer=init_worker,
                                 initargs=(tables, args.epsilons)) as pool:
            parts = list(pool.map(scan_chunk, chunks))
        e6 = e6_sstar(n)
        rows = []
        for q, eps in enumerate(args.epsilons):
            best = merge_max(parts, 0, q)
            low = merge_max(parts, 1, q)
            rnd = merge_max(parts, 2, q)
            # Compare the two optimization objects directly at E6 s*.
            e6_rec = None
            if e6 is not None:
                xi_e6 = pow(2, e6, 3 ** n)
                init_worker(tables, args.epsilons)
                avg, lo, hi = candidate_scores(xi_e6)[q]
                e6_rec = {"xi": xi_e6, "low_s": e6, "avg_black": avg,
                          "min_black": lo, "max_black": hi, "mean_white_prob": 1.0-avg}
            mc_targets = [("best", best)]
            if rnd is not None:
                mc_targets.append(("best_random", rnd))
            mc = {}
            # Two targets run concurrently; remaining workers are unnecessary here.
            with ProcessPoolExecutor(max_workers=min(len(mc_targets), args.workers)) as pool:
                futures = [(name, pool.submit(simulate_nwhite, n, rec["xi"], eps,
                                              args.mc_paths, 100000*n + q*100 + i))
                           for i, (name, rec) in enumerate(mc_targets)]
                for name, future in futures:
                    mc[name] = future.result()
            theoretical_mean = (n / 8.0) * (1.0 - best["avg_black"])
            row = {"epsilon": eps, "best": best, "best_low_power": low,
                   "best_random_unit": rnd, "e6_sstar": e6, "at_e6_sstar": e6_rec,
                   "s_adv_minus_s_e6": None if e6 is None or low is None else low["low_s"]-e6,
                   "theoretical_mean_Nwhite": theoretical_mean, "monte_carlo": mc}
            rows.append(row)
            print(f"n={n} eps={eps:g} Bcand={best['avg_black']:.6f} "
                  f"1-B={1-best['avg_black']:.6f} s_adv={low['low_s'] if low else None} "
                  f"s_E6={e6} random_B={rnd['avg_black'] if rnd else None:.6f} "
                  f"Mcos={mc['best']['moment_eta_cos']:.6f} "
                  f"Meps3={mc['best']['moment_eta_eps3']:.6f} "
                  f"zero={mc['best']['zero_fraction']:.5f}", flush=True)
        output.append({"n": n, "exhaustive": exhaustive,
                       "candidate_count": len(candidates), "rows": rows})
        Path(args.out).write_text(json.dumps({"params": vars(args), "results": output}, indent=2),
                                  encoding="utf-8")
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
