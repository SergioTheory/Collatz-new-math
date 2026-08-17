#!/usr/bin/env python3
"""Exhaustive forward restart/transport diagnostic modulo powers of two.

For odd N in [Y,2Y), follows d accelerated Syracuse steps, retains paths with
x_k>N0 for k<=d, and measures endpoint residues modulo 2^m globally and inside
dyadic endpoint buckets.  This is a finite-scale diagnostic, not a proof.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np


def scan_chunk(task):
    lo, hi, n0, d, max_m = task
    mod = 1 << max_m
    hist = np.zeros(mod, dtype=np.int64)
    buckets: dict[int, np.ndarray] = {}
    bucket_words: dict[int, set[tuple[int, ...]]] = {}
    survivors = 0
    words: set[tuple[int, ...]] = set()
    n = lo | 1
    while n < hi:
        x = n
        alive = x > n0
        word = []
        if alive:
            for _ in range(d):
                z = 3 * x + 1
                a = (z & -z).bit_length() - 1
                word.append(a)
                x = z >> a
                if x <= n0:
                    alive = False
                    break
        if alive:
            survivors += 1
            residue = x & (mod - 1)
            hist[residue] += 1
            bit_bucket = x.bit_length()
            if bit_bucket not in buckets:
                buckets[bit_bucket] = np.zeros(mod, dtype=np.int64)
            buckets[bit_bucket][residue] += 1
            word_tuple = tuple(word)
            words.add(word_tuple)
            bucket_words.setdefault(bit_bucket, set()).add(word_tuple)
        n += 2
    return survivors, hist, buckets, words, bucket_words


def fold_hist(hist: np.ndarray, m: int) -> np.ndarray:
    mod = 1 << m
    return hist.reshape(-1, mod).sum(axis=0)


def metrics(hist: np.ndarray) -> dict:
    """Compare with Haar measure on odd residue classes (endpoints are odd)."""
    total = int(hist.sum())
    mod = len(hist)
    odd_hist = hist[1::2]
    admissible = len(odd_hist)
    if total == 0:
        return {"total": 0, "modulus": mod, "admissible_odd_classes": admissible}
    expected = total / admissible
    max_ratio = float(odd_hist.max() / expected)
    min_ratio = float(odd_hist.min() / expected)
    tv = float(0.5 * np.abs(odd_hist / total - 1.0 / admissible).sum())
    chi2_per_df = float((((odd_hist - expected) ** 2 / expected).sum()) / max(1, admissible - 1))
    probabilities = odd_hist / total
    fourier = np.fft.fft(probabilities)
    nonzero = np.abs(fourier[1:]) if admissible > 1 else np.array([0.0])
    max_fourier = float(nonzero.max())
    argmax_fourier = int(nonzero.argmax() + 1)
    l2_fourier = float(np.sqrt(np.sum(nonzero ** 2)))
    return {
        "total": total,
        "modulus": mod,
        "admissible_odd_classes": admissible,
        "max_ratio": max_ratio,
        "min_ratio": min_ratio,
        "tv": tv,
        "chi2_per_df": chi2_per_df,
        "empty_fraction": float(np.mean(odd_hist == 0)),
        "even_mass": int(hist[0::2].sum()),
        "max_nonzero_fourier": max_fourier,
        "argmax_fourier": argmax_fourier,
        "l2_nonzero_fourier": l2_fourier,
        "iid_single_fourier_scale": float(1.0 / math.sqrt(total)),
    }


def run_config(n0_bits: int, alpha: float, max_m: int, workers: int):
    lam = math.log2(3)
    lower_t = (alpha - 1.0) / (2.0 - lam)
    upper_t = 1.0 / lam
    t = 0.5 * (lower_t + upper_t)
    n0 = 1 << n0_bits
    y_bits = math.ceil(alpha * n0_bits)
    y = 1 << y_bits
    d = max(1, math.floor(t * n0_bits))
    odd_count = y // 2
    chunk_odds = (odd_count + workers - 1) // workers
    tasks = []
    for i in range(workers):
        lo = y + 2 * i * chunk_odds
        hi = min(2 * y, lo + 2 * chunk_odds)
        if lo < hi:
            tasks.append((lo, hi, n0, d, max_m))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(scan_chunk, tasks, chunksize=1))
    mod = 1 << max_m
    hist = np.zeros(mod, dtype=np.int64)
    buckets: dict[int, np.ndarray] = {}
    survivors = 0
    words: set[tuple[int, ...]] = set()
    bucket_words: dict[int, set[tuple[int, ...]]] = {}
    for count, h, bb, ww, bww in parts:
        survivors += count
        hist += h
        words.update(ww)
        for bit, arr in bb.items():
            buckets.setdefault(bit, np.zeros(mod, dtype=np.int64))
            buckets[bit] += arr
        for bit, word_set in bww.items():
            bucket_words.setdefault(bit, set()).update(word_set)
    global_metrics = {}
    for m in range(1, max_m + 1):
        gm = metrics(fold_hist(hist, m))
        K = 1 << (m - 1)
        gm["active_words"] = len(words)
        gm["within_word_KW_over_Q_bound"] = K * len(words) / survivors if survivors else float("inf")
        gm["within_word_max_ratio_bound"] = 1.0 + gm["within_word_KW_over_Q_bound"]
        global_metrics[str(m)] = gm
    bucket_metrics = {}
    for bit, arr in sorted(buckets.items()):
        count = int(arr.sum())
        if count < 64:
            continue
        safe_max_m = min(max_m, max(1, int(math.log2(count)) - 3))
        bucket_metrics[str(bit)] = {}
        Wb = len(bucket_words.get(bit, set()))
        for m in range(1, safe_max_m + 1):
            bm = metrics(fold_hist(arr, m))
            K = 1 << (m - 1)
            bm["active_words"] = Wb
            bm["within_word_KW_over_Q_bound"] = K * Wb / count
            bm["within_word_max_ratio_bound"] = 1.0 + bm["within_word_KW_over_Q_bound"]
            bucket_metrics[str(bit)][str(m)] = bm
    sigma = lam + (alpha - 1.0) / t
    return {
        "n0_bits": n0_bits,
        "N0": n0,
        "alpha_requested": alpha,
        "Y_bits": y_bits,
        "Y": y,
        "d": d,
        "t": t,
        "sigma_threshold": sigma,
        "input_odd_count": odd_count,
        "survivors": survivors,
        "survival_fraction": survivors / odd_count,
        "distinct_active_words": len(words),
        "global": global_metrics,
        "endpoint_bit_buckets": bucket_metrics,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n0-bits", nargs="+", type=int, default=[14, 16, 18, 20])
    ap.add_argument("--alphas", nargs="+", type=float, default=[1.05, 1.10, 1.20])
    ap.add_argument("--max-m", type=int, default=14)
    ap.add_argument("--workers", type=int, default=min(30, os.cpu_count() or 1))
    ap.add_argument("--out", default="restart_transport_results.json")
    args = ap.parse_args()
    results = []
    for bits in args.n0_bits:
        for alpha in args.alphas:
            print(f"N0=2^{bits} alpha={alpha:.2f}", flush=True)
            row = run_config(bits, alpha, args.max_m, args.workers)
            results.append(row)
            m_show = min(args.max_m, 10)
            gm = row["global"][str(m_show)]
            print(
                f"  Y=2^{row['Y_bits']} d={row['d']} survivors={row['survivors']} "
                f"frac={row['survival_fraction']:.4g} m={m_show} "
                f"K={gm.get('max_ratio', float('nan')):.3f} TV={gm.get('tv', float('nan')):.3f}",
                flush=True,
            )
            Path(args.out).write_text(json.dumps({"params": vars(args), "results": results}, indent=2), encoding="utf-8")
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
