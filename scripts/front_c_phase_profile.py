#!/usr/bin/env python3
"""Exact conditioned phase profiles for Front C.

For each (n, xi, j), computes the NB(2(j-1),1/2)-weighted distribution of
  theta = xi * 2^{-(L_{j-1}+2)} / 3^(n-2j+2) (mod 1),
conditioned on b_j=3.  Reports black mass, binned TV/entropy, and low Fourier
harmonics.  This is a finite-n diagnostic, not an equidistribution proof.
"""
from __future__ import annotations

import argparse
import cmath
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from front_c_adversarial import nb_support


def profile_one(task):
    n, name, xi, j, eps, bins, harmonics = task
    k = n - 2 * j + 2
    mod = 3 ** k
    inv2 = (mod + 1) // 2
    hist = [0.0] * bins
    hs = [0j] * harmonics
    black = 0.0
    for l_prev, weight in nb_support(j):
        r = ((xi % mod) * pow(inv2, l_prev + 2, mod)) % mod
        d = min(r, mod - r)
        if d <= eps * mod:
            black += weight
        x = r / mod
        b = min(bins - 1, int(x * bins))
        hist[b] += weight
        z = cmath.exp(2j * math.pi * x)
        zh = z
        for h in range(harmonics):
            hs[h] += weight * zh
            zh *= z
    uniform = 1.0 / bins
    tv = 0.5 * sum(abs(v - uniform) for v in hist)
    entropy = -sum(v * math.log(v) for v in hist if v > 0) / math.log(bins)
    max_bin_ratio = max(hist) / uniform
    return {
        "n": n, "name": name, "xi": xi, "j": j, "j_fraction": j / (n / 2),
        "k": k, "modulus": mod, "black": black, "white": 1.0 - black,
        "tv_binned_uniform": tv, "normalized_bin_entropy": entropy,
        "max_bin_over_uniform": max_bin_ratio,
        "harmonics_abs": [abs(z) for z in hs], "histogram": hist,
    }


def load_targets(results_path: Path, n: int, eps: float):
    data = json.loads(results_path.read_text(encoding="utf-8"))
    result = next(r for r in data["results"] if r["n"] == n)
    row = next(r for r in result["rows"] if abs(r["epsilon"] - eps) < 1e-15)
    targets = {
        "resonant_adv": row["best_low_power"]["xi"],
        "bulk_sample_worst": row["best_random_unit"]["xi"],
    }
    if row["at_e6_sstar"] is not None:
        targets["e6_worst"] = row["at_e6_sstar"]["xi"]
    return targets, row


def summarize(records, n, name):
    rr = sorted((r for r in records if r["n"] == n and r["name"] == name), key=lambda r: r["j"])
    m = len(rr)
    deciles = []
    for q in range(10):
        block = rr[q*m//10:(q+1)*m//10]
        deciles.append({
            "decile": q + 1,
            "j_start": block[0]["j"], "j_end": block[-1]["j"],
            "mean_black": sum(r["black"] for r in block) / len(block),
            "mean_tv": sum(r["tv_binned_uniform"] for r in block) / len(block),
            "mean_h1": sum(r["harmonics_abs"][0] for r in block) / len(block),
        })
    top_black = sorted(rr, key=lambda r: r["black"], reverse=True)[:10]
    top_tv = sorted(rr, key=lambda r: r["tv_binned_uniform"], reverse=True)[:10]
    return {
        "n": n, "name": name,
        "mean_black": sum(r["black"] for r in rr) / m,
        "mean_tv": sum(r["tv_binned_uniform"] for r in rr) / m,
        "mean_harmonics_abs": [sum(r["harmonics_abs"][h] for r in rr) / m
                               for h in range(len(rr[0]["harmonics_abs"]))],
        "deciles": deciles,
        "top_black_j": [{"j": r["j"], "k": r["k"], "black": r["black"],
                          "tv": r["tv_binned_uniform"]} for r in top_black],
        "top_tv_j": [{"j": r["j"], "k": r["k"], "black": r["black"],
                       "tv": r["tv_binned_uniform"]} for r in top_tv],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", nargs="+", type=int, default=[200, 400])
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--bins", type=int, default=100)
    ap.add_argument("--harmonics", type=int, default=20)
    ap.add_argument("--workers", type=int, default=min(30, os.cpu_count() or 1))
    ap.add_argument("--source", default="front_c_large_results.json")
    ap.add_argument("--out", default="front_c_phase_profiles.json")
    args = ap.parse_args()

    source = Path(args.source)
    tasks = []
    metadata = {}
    for n in args.ns:
        targets, row = load_targets(source, n, args.eps)
        metadata[n] = {"targets": targets, "s_adv": row["best_low_power"]["low_s"],
                       "s_e6": row["e6_sstar"]}
        for name, xi in targets.items():
            for j in range(1, n // 2 + 1):
                tasks.append((n, name, xi, j, args.eps, args.bins, args.harmonics))
    print(f"profiling {len(tasks)} exact (n,xi,j) tasks on {args.workers} workers", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(profile_one, tasks, chunksize=max(1, len(tasks)//(args.workers*8))))

    summaries = []
    for n in args.ns:
        for name in metadata[n]["targets"]:
            s = summarize(records, n, name)
            summaries.append(s)
            print(f"n={n} {name}: B={s['mean_black']:.6f} TV={s['mean_tv']:.6f} "
                  f"h1={s['mean_harmonics_abs'][0]:.6f}", flush=True)
            print("  black by j-decile:", " ".join(f"{d['mean_black']:.3f}" for d in s["deciles"]), flush=True)

    Path(args.out).write_text(json.dumps({"params": vars(args), "metadata": metadata,
                                         "summaries": summaries, "profiles": records}, indent=2),
                              encoding="utf-8")
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
