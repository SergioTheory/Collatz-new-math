#!/usr/bin/env python3
"""E8 Step 2b: extended-grid low-a suppression tests (exact, vectorized).

Column A (realistic regime d2 ~ M/2):   M in {24,26,28,30,32}, d2 = M/2.
Column B (E8-pattern continuation):     M in {32,40,48,60},   d2 = M-6.
A-sweep (C(A) transition):              (M,d2) in {(24,12),(26,13),(28,14)},
                                        A in {16,64,128,256,512,1024}.

Exact batch computation of beta(h) = 2^{-M} sum_w exp(-2 pi i h r_w / 2^M)
for all low-a h (union over d1 in {4,6,8,10}), via the vectorized residue
recurrence  c <- 3c + 2^s,  s += a_j  (mod 2^{M+1}).
"""
from __future__ import annotations

import argparse
import itertools
import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from e8_low_a_test import low_a_hs


def batch_words(M: int, d: int, batch: int):
    """Yield numpy arrays of shape (<=batch, d): compositions of M into d parts."""
    if d == 1:
        yield np.full((1, 1), M, dtype=np.int64)
        return
    it = itertools.combinations(range(1, M), d - 1)
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            return
        cuts = np.asarray(chunk, dtype=np.int64)          # (b, d-1)
        b = cuts.shape[0]
        full = np.concatenate([cuts, np.full((b, 1), M, dtype=np.int64)], axis=1)
        shift = np.concatenate([np.zeros((b, 1), dtype=np.int64), full[:, :-1]], axis=1)
        yield full - shift


def residues_batch(words: np.ndarray, M: int, inv3d: int):
    """r_w mod 2^M for each row of words (exact, int64, mod 2^{M+1})."""
    mod = 1 << (M + 1)
    mask = mod - 1
    c = np.zeros(words.shape[0], dtype=np.int64)
    s = np.zeros(words.shape[0], dtype=np.int64)
    for j in range(words.shape[1]):
        a = words[:, j]
        c = (3 * c + np.left_shift(np.int64(1), s)) & mask
        s = s + a
    rho = (((1 << M) - c) * inv3d) & mask
    return ((rho - 1) >> 1) & ((1 << M) - 1)


def hr_mod(h: int, r: np.ndarray, M: int):
    """(h * r) mod 2^M for vector r, avoiding int64 overflow (M <= 62)."""
    hb = M // 2
    hmask = (1 << M) - 1
    h0 = h & ((1 << hb) - 1)
    h1 = h >> hb
    r0 = r & ((1 << hb) - 1)
    r1 = r >> hb
    cross = ((h1 * r0 + h0 * r1) & ((1 << hb) - 1)) << hb
    return (cross + (h0 * r0)) & hmask


BATCH = 250_000
HCHUNK = 16


def case_run(args):
    M, d2, d1s, A, skip, limit = args
    hs = sorted({h for d1 in d1s for h in low_a_hs(M, d1, A)})
    H = len(hs)
    inv3d = pow(3, -d2, 1 << (M + 1))
    scale = -2.0 * math.pi / (1 << M)
    acc = np.zeros(H, dtype=np.complex64)
    half = 1 << (M - 1)
    hmask = (1 << M) - 1
    fast = M <= 32  # single uint64 multiply path
    n_batches = 0
    for words in batch_words(M, d2, BATCH):
        if n_batches < skip:
            n_batches += 1
            continue
        if limit is not None and n_batches >= skip + limit:
            break
        n_batches += 1
        r = residues_batch(words, M, inv3d)
        if fast:
            ru = r.astype(np.uint64)
            for lo in range(0, H, HCHUNK):
                hi = min(lo + HCHUNK, H)
                hu = np.asarray(hs[lo:hi], dtype=np.uint64)[:, None]
                hr = (hu * ru[None, :]) & hmask
                phase = (scale * hr).astype(np.float32)
                acc[lo:hi] += np.exp(1j * phase).sum(axis=1)
        else:
            hb = M // 2
            lb = (1 << hb) - 1
            r0 = r & lb
            r1 = r >> hb
            for lo in range(0, H, HCHUNK):
                hi = min(lo + HCHUNK, H)
                hs_arr = np.asarray(hs[lo:hi], dtype=np.int64)
                h0 = (hs_arr & lb)[:, None]
                h1 = (hs_arr >> hb)[:, None]
                cross = ((h1 * r0[None, :] + h0 * r1[None, :]) & lb) << hb
                hr = (cross + h0 * r0[None, :]) & hmask
                phase = scale * hr.astype(np.float64)
                acc[lo:hi] += np.exp(1j * phase).sum(axis=1)
            del r0, r1
        del words, r
    absb = np.abs(acc) / (1 << M)
    i = int(np.argmax(absb))
    hmax = hs[i]
    amin = None
    for d1 in d1s:
        a_raw = (hmax * pow(3, d1, half)) % half
        a_signed = a_raw if a_raw <= half // 2 else a_raw - half
        amin = a_signed if amin is None else min(amin, a_signed, key=abs)
    W = math.comb(M - 1, d2 - 1)
    return {
        "M": M, "d2": d2, "A": A, "W": W, "num_h": H,
        "acc": acc,
        "hs": hs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d1s", nargs="+", type=int, default=[4, 6, 8, 10])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--colA", action="store_true", help="column A: d2=M/2, M=24..32")
    ap.add_argument("--colB", action="store_true", help="column B: d2=M-6, M=32,40,48,60")
    ap.add_argument("--asweep", action="store_true", help="A sweep at (24,12),(26,13),(28,14)")
    ap.add_argument("--amax", type=int, default=1024, help="cap A in --asweep")
    ap.add_argument("--asweep2", action="store_true", help="deep A sweep: M=24 A=2k..8k, M=26 A=2k..4k")
    ap.add_argument("--A", type=int, default=64)
    ap.add_argument("--slices", type=int, default=1, help="split each case into N slices")
    ap.add_argument("--M-list", nargs="+", type=int, default=None, help="override colA M values")
    args = ap.parse_args()

    cases = []
    if args.colA:
        for M in (args.M_list if args.M_list else (24, 26, 28, 30, 32)):
            cases.append((M, M // 2, args.d1s, args.A))
    if args.colB:
        for M in (32, 40, 48, 60):
            cases.append((M, M - 6, args.d1s, args.A))
    if args.asweep:
        for M, d2 in ((24, 12), (26, 13), (28, 14)):
            for A in (16, 64, 128, 256, 512, 1024):
                if A <= args.amax:
                    cases.append((M, d2, args.d1s, A))
    if args.asweep2:
        for M, d2, As in ((24, 12, (2048, 4096, 8192)), (26, 13, (2048, 4096))):
            for A in As:
                cases.append((M, d2, args.d1s, A))
    if not cases:
        ap.error("need at least one of --colA --colB --asweep")

    jobs = []
    for c in cases:
        M, d2, d1s, A = c
        n_batches = math.ceil(math.comb(M - 1, d2 - 1) / BATCH)
        per = max(1, math.ceil(n_batches / args.slices))
        for k in range(0, n_batches, per):
            jobs.append((M, d2, d1s, A, k, min(per, n_batches - k)))

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for r in pool.map(case_run, jobs):
            results.append(r)

    # merge slices with identical (M, d2, A): sum the partial accumulators
    merged = {}
    for r in results:
        key = (r["M"], r["d2"], r["A"])
        if key not in merged:
            merged[key] = dict(r)
        else:
            m = merged[key]
            m["acc"] = m["acc"] + r["acc"]
    results = []
    for r in merged.values():
        acc = r.pop("acc")
        hs = r["hs"]
        absb = np.abs(acc) / (1 << r["M"])
        i = int(np.argmax(absb))
        half = 1 << (r["M"] - 1)
        amin = None
        for d1 in args.d1s:
            a_raw = (hs[i] * pow(3, d1, half)) % half
            a_signed = a_raw if a_raw <= half // 2 else a_raw - half
            amin = a_signed if amin is None else min(amin, a_signed, key=abs)
        r["max_abs_beta"] = float(absb[i])
        r["max_h"] = hs[i]
        r["a_of_max"] = amin
        r["ratio_2m2"] = float(absb[i] * 2.0 ** (r["M"] / 2))
        r["ratio_sqrtW"] = float(absb[i] * 2.0 ** r["M"] / math.sqrt(r["W"]))
        results.append(r)

    print(f"d1s={args.d1s}  (union of low-a h over all d1)")
    print(f"{'M':>3} {'d2':>3} {'A':>5} {'W':>11} {'#h':>5} {'max|b|':>12} "
          f"{'max|b|*2^(M/2)':>16} {'|F|/sqrtW':>12} {'argmax h':>12} {'a':>5}")
    for r in sorted(results, key=lambda r: (r["M"], r["d2"], r["A"])):
        print(f"{r['M']:>3} {r['d2']:>3} {r['A']:>5} {r['W']:>11} {r['num_h']:>5} "
              f"{r['max_abs_beta']:>12.3e} {r['ratio_2m2']:>16.4f} "
              f"{r['ratio_sqrtW']:>12.4f} {r['max_h']:>12} {r['a_of_max']:>5}")

    for M, d2 in sorted({(r["M"], r["d2"]) for r in results}):
        rows = [r for r in results if r["M"] == M and r["d2"] == d2]
        if len(rows) > 1:
            seq = " ".join(f"A={r['A']}:{r['ratio_2m2']:.2f}" for r in rows)
            print(f"M={M} d2={d2}  C(A) trend (max|b|*2^(M/2)): {seq}")


if __name__ == "__main__":
    main()