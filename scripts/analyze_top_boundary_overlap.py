#!/usr/bin/env python3
"""Compare endpoint and top boundary-layer spectra in co-moving coordinates."""
from __future__ import annotations
import argparse
import math
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from restart_bad_spectral_overlap import endpoints_chunk, schedule, build_bad


def signed_residue(a: int, modulus: int) -> int:
    a %= modulus
    return a if a <= modulus // 2 else a - modulus


def top_odd(values: np.ndarray, top: int):
    odd_values = values[1:-1:2]
    n = min(top, len(odd_values))
    selected = np.argpartition(odd_values, len(odd_values) - n)[-n:]
    selected = selected[np.lexsort((selected, -odd_values[selected]))]
    return [2 * int(i) + 1 for i in selected]


def endpoint_counts(B: int, alpha: float, target_bit: int, workers: int):
    n0 = 1 << B
    ybits = math.ceil(alpha * B)
    Y = 1 << ybits
    lam = math.log2(3)
    t = 0.5 * ((alpha - 1) / (2 - lam) + 1 / lam)
    d1 = max(1, math.floor(t * B))
    count = Y // 2
    per = (count + workers - 1) // workers
    tasks = []
    for i in range(workers):
        lo = Y + 2 * i * per
        hi = min(2 * Y, lo + 2 * per)
        if lo < hi:
            tasks.append((lo, hi, n0, d1, B))
    parts = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(endpoints_chunk, tasks, chunksize=1):
            if target_bit in result:
                parts.append(result[target_bit])
    d2, M, _ = schedule(B, target_bit)
    K = 1 << M
    indices = np.concatenate(parts)
    counts = np.bincount(indices, minlength=K).astype(np.float64)
    return counts, d1, d2, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=20)
    ap.add_argument("--alpha", type=float, default=1.10)
    ap.add_argument("--bit", type=int, default=25)
    ap.add_argument("--workers", type=int, default=min(30, os.cpu_count() or 1))
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    counts, d1, d2, M = endpoint_counts(args.B, args.alpha, args.bit, args.workers)
    K = 1 << M
    Q = int(counts.sum())
    nu = counts / Q
    print(f"B={args.B} alpha={args.alpha} bit={args.bit} Q={Q} d1={d1} d2={d2} M={M} K={K}")
    bad = build_bad(K, d2, M, args.workers)
    direct = float(np.dot(nu, bad))
    fresh = float(bad.mean())
    fnu = np.fft.rfft(nu)
    beta = np.fft.rfft(bad) / K
    endpoint_abs = np.abs(fnu)
    beta_abs = np.abs(beta)
    endpoint_top = top_odd(endpoint_abs, args.top)
    beta_top = top_odd(beta_abs, args.top)
    multiplier = pow(3, d1, K)

    def row(h: int):
        pair = 2.0 * float((fnu[h] * np.conj(beta[h])).real)
        return (
            h,
            float(endpoint_abs[h]),
            float(beta_abs[h]),
            signed_residue(h * multiplier, K),
            signed_residue(h * multiplier, K // 2),
            pair,
        )

    print(f"direct_difference={direct-fresh:+.12g}")
    print("top endpoint odd: rank h endpoint_abs beta_abs a_mod_2^M a_mod_2^(M-1) pair")
    for rank, h in enumerate(endpoint_top, 1):
        print(rank, *row(h))
    print("top beta odd: rank h endpoint_abs beta_abs a_mod_2^M a_mod_2^(M-1) pair")
    for rank, h in enumerate(beta_top, 1):
        print(rank, *row(h))

    endpoint100 = set(top_odd(endpoint_abs, 100))
    beta100 = set(top_odd(beta_abs, 100))
    print("top100_frequency_intersection", len(endpoint100 & beta100), sorted(endpoint100 & beta100)[:20])
    odd_pairs = 2.0 * (fnu[1:-1:2] * np.conj(beta[1:-1:2])).real
    print("full_odd_pairing", "signed", float(odd_pairs.sum()), "l1", float(np.abs(odd_pairs).sum()))

    inv_multiplier = pow(multiplier, -1, K)
    print("low positive odd co-moving a: a h endpoint_abs beta_abs pair")
    for a in range(1, 32, 2):
        h = (a * inv_multiplier) % K
        if h > K // 2:
            h = K - h
        print(a, *row(h)[:3], row(h)[5])

    for cutoff in (31, 127, 511, 2047, 8191):
        hs = []
        for a in range(1, cutoff + 1, 2):
            h = (a * inv_multiplier) % K
            if h > K // 2:
                h = K - h
            hs.append(h)
        hs = np.asarray(hs, dtype=np.int64)
        pairs = 2.0 * (fnu[hs] * np.conj(beta[hs])).real
        print(
            "low_a_summary",
            cutoff,
            "count",
            len(hs),
            "signed",
            float(pairs.sum()),
            "l1",
            float(np.abs(pairs).sum()),
            "max_endpoint",
            float(endpoint_abs[hs].max()),
            "max_beta",
            float(beta_abs[hs].max()),
        )


if __name__ == "__main__":
    main()
