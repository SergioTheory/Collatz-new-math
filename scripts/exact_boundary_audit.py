#!/usr/bin/env python3
"""Exact integer restart audit plus selected high-precision boundary sums.

The dot-product audit is exact over integers.  High-precision beta values are
computed only at selected frequencies; an all-frequency mpmath DFT is not a
feasible exact audit at K=2^24.
"""
from __future__ import annotations
import argparse
import itertools
import math
import os
from fractions import Fraction
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import mpmath as mp
from restart_bad_spectral_overlap import endpoints_chunk, schedule, bad_chunk


def endpoint_parts(B, alpha, workers):
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
    merged = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(endpoints_chunk, tasks, chunksize=1):
            for bit, values in result.items():
                merged.setdefault(bit, []).append(values)
    return merged, d1


def build_bad_exact(K, d, M, workers):
    per = (K + workers - 1) // workers
    tasks = [(i, min(K, i + per), d, M) for i in range(0, K, per)]
    out = np.zeros(K, dtype=np.uint8)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for lo, values in pool.map(bad_chunk, tasks, chunksize=1):
            out[lo:lo + len(values)] = values
    return out


def compositions(total, length):
    for cuts in itertools.combinations(range(1, total), length - 1):
        prev = 0
        word = []
        for cut in cuts + (total,):
            word.append(cut - prev)
            prev = cut
        yield word


def compositions_desc(total, length):
    if length == 1:
        yield [total]
        return
    for first in range(total - length + 1, 0, -1):
        for rest in compositions_desc(total - first, length - 1):
            yield [first] + rest


def word_residue(word):
    c = 0
    s = 0
    for a in word:
        c = 3 * c + (1 << s)
        s += a
    rho = ((1 << s) - c) * pow(3, -len(word), 1 << (s + 1)) % (1 << (s + 1))
    return (rho - 1) // 2


def direct_beta_mp(M, d, h, precision, reverse=False):
    K = 1 << M
    mp.mp.dps = precision
    scale = -2 * mp.pi * h / K
    total = mp.mpc(0)
    words = compositions_desc(M, d) if reverse else compositions(M, d)
    for word in words:
        r = word_residue(word)
        total += mp.exp(1j * scale * r)
    return total / K


def top_odd(f, top):
    vals = np.abs(f[1:-1:2])
    n = min(top, len(vals))
    ids = np.argpartition(vals, len(vals) - n)[-n:]
    ids = ids[np.lexsort((ids, -vals[ids]))]
    return [2 * int(i) + 1 for i in ids]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases', nargs='+', type=int, default=[16, 18, 20])
    ap.add_argument('--alpha', type=float, default=1.10)
    ap.add_argument('--workers', type=int, default=min(30, os.cpu_count() or 1))
    ap.add_argument('--direct-top', type=int, default=3)
    ap.add_argument('--mp-dps', type=int, default=60)
    args = ap.parse_args()

    for B in args.cases:
        merged, d1 = endpoint_parts(B, args.alpha, args.workers)
        total_Q = 0
        weighted_num = Fraction(0, 1)
        print(f'B={B} alpha={args.alpha} d1={d1}')
        target = None
        for bit, pieces in sorted(merged.items()):
            d2, M, _ = schedule(B, bit)
            K = 1 << M
            counts = np.bincount(np.concatenate(pieces), minlength=K).astype(np.int64)
            bad = build_bad_exact(K, d2, M, args.workers)
            Q = int(counts.sum())
            bad_count = int(bad.sum())
            numerator = int(np.dot(counts, bad.astype(np.int64)))
            delta = Fraction(numerator, Q) - Fraction(bad_count, K)
            total_Q += Q
            weighted_num += abs(delta) * Q
            print(
                f' bit={bit} d={d2} M={M} K={K} Q={Q} '
                f'delta={float(delta):+.12g} exact={delta.numerator}/{delta.denominator} '
                f'fresh={bad_count}/{K}'
            )
            if B == 20 and bit == 25:
                target = (counts, bad, d2, M, Q, numerator, delta)
            del counts, bad
        print(f' weighted_abs={float(weighted_num/total_Q):.12g}')

        if target is not None:
            counts, bad, d2, M, Q, numerator, delta = target
            K = 1 << M
            nu = counts.astype(np.float64) / Q
            fft_nu = np.fft.rfft(nu)
            fft_beta = np.fft.rfft(bad.astype(np.float64)) / K
            hs = top_odd(fft_nu, args.direct_top)
            print('selected_beta_direct')
            for h in hs:
                z = direct_beta_mp(M, d2, h, args.mp_dps)
                z_fft = complex(fft_beta[h])
                print(
                    f' h={h} beta_mp={mp.nstr(z, 25)} '
                    f'beta_fft={z_fft.real:+.16g}{z_fft.imag:+.16g}j '
                    f'abs_diff_float={abs(complex(z.real, z.imag)-z_fft):.3e}'
                )
            mu = Fraction(int(bad.sum()), K)
            print('parseval_exact total=', f'{mu.numerator}/{mu.denominator}', float(mu))
            print('parseval_exact nonzero=', f'{(mu*(1-mu)).numerator}/{(mu*(1-mu)).denominator}', float(mu*(1-mu)))


if __name__ == '__main__':
    main()
