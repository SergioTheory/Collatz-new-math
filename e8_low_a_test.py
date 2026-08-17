#!/usr/bin/env python3
"""E8 Step 1: numerical verification of the low-a suppression bound.

Claim to test (Qwen, task E8): for odd h with co-moving coordinate
    a = h * 3^{d1} mod 2^{M-1},  |a| <= A,
we should have
    |beta_{d2,M}(h)| <= C(A) * 2^{-M/2} * poly(M),
where beta_{d2,M}(h) = 2^{-M} * sum_{w in N^d2, |w|=M} exp(-2 pi i h r_w / 2^M)
and r_w is the exact odd-start residue in the z-coordinate.

Grid: d2 in {8,10,12,14,16,18}, M in {d2+4, d2+6, d2+8}, A=64.
d1 is swept over {4,6,8,10} and we report the worst case (the bound must be
uniform over the generated class, so we take the sup over d1 as well).
"""
from __future__ import annotations

import argparse
import itertools
import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np


def compositions(M: int, d: int):
    """Yield all compositions of M into d positive parts (descending cut order)."""
    if d == 1:
        yield (M,)
        return
    for cuts in itertools.combinations(range(1, M), d - 1):
        prev = 0
        out = []
        for cut in cuts + (M,):
            out.append(cut - prev)
            prev = cut
        yield tuple(out)


def word_residue(word):
    """Exact odd-start residue r_w mod 2^S in the z-coordinate (N=2z+1).

    rho_w = (2^S - c_w) * 3^{-d} mod 2^{S+1},  r_w = (rho_w - 1)/2.
    """
    c = 0
    s = 0
    for a in word:
        c = 3 * c + (1 << s)
        s += a
    rho = ((1 << s) - c) * pow(3, -len(word), 1 << (s + 1)) % (1 << (s + 1))
    assert rho & 1
    return (rho - 1) // 2


def residues_for(M: int, d: int):
    """All r_w mod 2^M for words of length d and weight M (as int64 array)."""
    rs = []
    for word in compositions(M, d):
        rs.append(word_residue(word))
    arr = np.asarray(rs, dtype=np.int64)
    assert len(np.unique(arr)) == len(arr), "top-layer residues must be distinct"
    return arr


def beta_at_h(res: np.ndarray, M: int, h: int):
    """beta_{d,M}(h) = 2^{-M} sum_w exp(-2 pi i h r_w / 2^M), as complex."""
    scale = -2.0 * math.pi * h / (1 << M)
    phase = scale * res.astype(np.float64)
    return np.exp(1j * phase).sum() / (1 << M)


def low_a_hs(M: int, d1: int, A: int):
    """Odd h in [0,2^M) with signed co-moving |a|<=A, a=h*3^{d1} mod 2^{M-1}.

    For each odd a with |a|<=A, h0 = a*3^{-d1} mod 2^{M-1} is the base lift;
    both lifts h0 and h0+2^{M-1} mod 2^M are odd and are tested.
    """
    half = 1 << (M - 1)
    inv = pow(3, -d1, half)
    hs = []
    # h odd and 3^{d1} odd  =>  a = h*3^{d1} mod 2^{M-1} is odd.
    for a in range(-A + 1, A + 1, 2):
        if a == 0:
            continue
        h0 = (a * inv) % half
        assert h0 & 1
        for h in (h0, h0 + half):
            if h & 1:
                hs.append(h % (half << 1))
    return hs


def run_case(args):
    M, d2, d1s, A = args
    res = residues_for(M, d2)
    W = len(res)
    half = 1 << (M - 1)
    hs = set()
    for d1 in d1s:
        hs.update(low_a_hs(M, d1, A))
    hs = sorted(hs)
    betas = [beta_at_h(res, M, h) for h in hs]
    absb = np.abs(np.asarray(betas))
    i = int(np.argmax(absb))
    hmax = hs[i]
    amin = None
    for d1 in d1s:
        a_raw = (hmax * pow(3, d1, half)) % half
        a_signed = a_raw if a_raw <= half // 2 else a_raw - half
        amin = a_signed if amin is None else min(amin, a_signed, key=abs)
    return {
        "M": M,
        "d2": d2,
        "W": W,
        "num_h": len(hs),
        "max_abs_beta": float(absb[i]),
        "max_h": hmax,
        "a_of_max": amin,
        "ratio_2m2": float(absb[i] * 2.0 ** (M / 2)),
        "ratio_2m2_M": float(absb[i] * 2.0 ** (M / 2) * M),
        "ratio_sqrtW": float(absb[i] * 2.0 ** M / math.sqrt(W)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--A", type=int, default=64)
    ap.add_argument("--d1s", nargs="+", type=int, default=[4, 6, 8, 10])
    ap.add_argument("--d2s", nargs="+", type=int, default=[8, 10, 12, 14, 16, 18])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    cases = []
    for d2 in args.d2s:
        for M in (d2 + 4, d2 + 6, d2 + 8):
            cases.append((M, d2, args.d1s, args.A))

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for r in pool.map(run_case, cases):
            results.append(r)

    print(f"A={args.A}  d1s={args.d1s}  (union of low-a h over all d1, tested)")
    print(f"{'M':>3} {'d2':>3} {'W':>9} {'#h':>5} {'max|b|':>12} {'max|b|*2^(M/2)':>16} "
          f"{'...*M':>12} {'|F|/sqrtW':>12} {'argmax h':>10} {'a':>5}")
    worst_ratio = 0.0
    worst_row = None
    for r in sorted(results, key=lambda r: (r["M"], r["d2"])):
        m2 = r["ratio_2m2"]
        print(f"{r['M']:>3} {r['d2']:>3} {r['W']:>9} {r['num_h']:>5} "
              f"{r['max_abs_beta']:>12.3e} {m2:>16.4f} {r['ratio_2m2_M']:>12.4f} "
              f"{r['ratio_sqrtW']:>12.4f} {r['max_h']:>10} {r['a_of_max']:>5}")
        if m2 > worst_ratio:
            worst_ratio = m2
            worst_row = r

    print("\nWorst normalized |b|*2^(M/2) over grid:", f"{worst_ratio:.4f}")
    if worst_row:
        print("attained at M={} d2={} W={}".format(
            worst_row["M"], worst_row["d2"], worst_row["W"]))


if __name__ == "__main__":
    main()