#!/usr/bin/env python3
"""Exact collision and odd-frequency tests for the top valuation layer."""
from __future__ import annotations
import argparse
import itertools
import math
from collections import Counter
import numpy as np


def compositions(total: int, length: int):
    if length == 1:
        yield (total,)
        return
    for cuts in itertools.combinations(range(1, total), length - 1):
        prev = 0
        out = []
        for cut in cuts + (total,):
            out.append(cut - prev)
            prev = cut
        yield tuple(out)


def residue(word):
    c = 0
    s = 0
    for a in word:
        c = 3 * c + (1 << s)
        s += a
    rho = ((1 << s) - c) * pow(3, -len(word), 1 << (s + 1)) % (1 << (s + 1))
    assert rho & 1
    return (rho - 1) // 2


def phase_recursion_check(word):
    prefix = ()
    r_prev = 0
    s_prev = 0
    rows = []
    for a in word:
        prefix = prefix + (a,)
        r_new = residue(prefix)
        modulus = 1 << (s_prev + a)
        assert (r_new - r_prev) % (1 << s_prev) == 0
        t = ((r_new - r_prev) >> s_prev) % (1 << a) if s_prev else r_new % (1 << a)
        assert (r_prev + (1 << s_prev) * t) % modulus == r_new
        # At the new word's top modulus M=s_prev+a the phase increment is e(ht/2^a).
        for h in (1, 3, 5, 7):
            lhs = np.exp(2j * np.pi * h * r_new / modulus)
            rhs = np.exp(2j * np.pi * h * r_prev / modulus) * np.exp(2j * np.pi * h * t / (1 << a))
            assert abs(lhs - rhs) < 1e-12
        rows.append((s_prev, a, t))
        r_prev = r_new
        s_prev += a
    return rows


def case(total: int, length: int):
    rs = []
    recursion_rows = None
    for word in compositions(total, length):
        if recursion_rows is None:
            recursion_rows = phase_recursion_check(word)
        rs.append(residue(word))
    rs = np.asarray(rs, dtype=np.int64)
    words = len(rs)
    K = 1 << total
    assert len(np.unique(rs)) == words, "same-weight exact cylinders must be disjoint mod 2^M"
    hist = np.bincount(rs, minlength=K)
    antipodal_pairs = int(np.dot(hist, np.roll(hist, K // 2)))
    fft = np.fft.fft(hist.astype(float))
    rows = []
    for k in range(1, total + 1):
        h = np.bincount(rs % (1 << k), minlength=1 << k)
        ordered_offdiag = int(np.sum(h * (h - 1)))
        expected_offdiag = words * (words - 1) / (1 << k)
        rows.append({
            "k": k,
            "delta": total - k,
            "max_count": int(h.max()),
            "max_abs_dev": float(np.max(np.abs(h - words / (1 << k)))),
            "ordered_offdiag": ordered_offdiag,
            "uniform_offdiag": expected_offdiag,
            "offdiag_ratio": float(ordered_offdiag / expected_offdiag) if expected_offdiag else None,
        })
    odd = np.abs(fft[1::2])
    odd_h = np.arange(1, K, 2)
    odd_sq = odd * odd
    offdiag_fourier = odd_sq - words
    imax = int(np.argmax(odd))
    return {
        "M": total,
        "d": length,
        "words": words,
        "expected_occupancy": words / K,
        "antipodal_pairs": antipodal_pairs,
        "antipodal_over_words": antipodal_pairs / words,
        "exact_top_layer_collisions": int(np.sum(hist * (hist - 1))),
        "phase_recursion_sample": recursion_rows,
        "collision_by_k": rows,
        "odd_frequency": {
            "count": int(len(odd)),
            "max_h": int(odd_h[imax]),
            "max_abs": float(odd[imax]),
            "max_abs_over_words": float(odd.max() / words),
            "rms_abs_over_words": float(np.sqrt(np.mean(odd_sq)) / words),
            "mean_offdiag": float(np.mean(offdiag_fourier)),
            "max_abs_offdiag": float(np.max(np.abs(offdiag_fourier))),
            "pointwise_collision_bound_ratio": float(odd_sq[imax] / words),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", default=["12:7", "14:8", "16:9", "18:10", "20:11"])
    args = ap.parse_args()
    for spec in args.cases:
        m, d = map(int, spec.split(":"))
        result = case(m, d)
        print(f"M={m} d={d} words={result['words']} expected_occ={result['expected_occupancy']:.6g} antipodal={result['antipodal_pairs']} ({result['antipodal_over_words']:.6g} W)")
        print(" odd", result["odd_frequency"])
        for row in result["collision_by_k"]:
            if row["delta"] in (0, 1, 2, 4, 8) or row["k"] == 1:
                print(" k", row)


if __name__ == "__main__":
    main()
