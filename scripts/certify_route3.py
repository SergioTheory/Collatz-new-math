"""
certify_route3.py — Route 3 certification constants (Theorem T3 of the paper).

Part A — ANALYTIC (exact closed forms, no simulation):
  * I2(sigma) : Cramer rate of Geom(1/2) in BITS.  For sigma in (1,2) the
    optimizer is exact:  e^s = 2 - 2/sigma  =>
        I2(sigma) = [ s*sigma - ln(e^s/(2 - e^s)) ] / ln 2.
    Known values:  I2(4/3) = log_2(3) - 4/3 = 0.2516..., I2(1) = 1, I2(2) = 0.
  * c_star(d, sigma) = 2^(-d * I2(sigma)) : per-block survival upper bound.
  * H2(x) : binary entropy in bits.  delta_d = alpha - sigma*t*H2(1/sigma)
    (the resolution-floor parameter gap).

Part B — EMPIRICAL (numba, 30 threads on E5-2696v3):
  One-block survival fraction of a window of `M` odd starts
      { N0, N0+2, N0+4, ..., N0 + 2(M-1) }
  under the accelerated map over `d` odd steps (orbit stays >= N0 for all d
  steps).  Cross-checked against the theoretical c_star and the Gate-2 band
  [0.51, 0.56] from the paper.

Writes data/route3_certificate.json
"""
import math
import json
import os
import time

import numpy as np
from numba import njit, prange, set_num_threads

# ---------------------------------------------------------------- analytics

def i2_bits(sigma: float) -> float:
    """Cramer rate of Geom(1/2) in bits, sigma in [1,2]. Exact closed form."""
    if sigma <= 1.0:
        return 1.0
    if sigma >= 2.0:
        return 0.0
    ln2 = math.log(2.0)
    es = 2.0 - 2.0 / sigma          # e^s
    if es <= 0:
        return 1.0
    s = math.log(es)
    lam = math.log(es / (2.0 - es))  # Lambda(s) in nats
    return (s * sigma - lam) / ln2


def c_star_bits(d: int, sigma: float) -> float:
    return 2.0 ** (-d * log2_bits(sigma))


def log2_bits(sigma: float) -> float:
    return log2_bits_impl(sigma) if False else log2_bits_exact(sigma)


def log2_bits_exact(sigma: float) -> float:
    # alias kept for readability; the exact one is `log2_bits` via `i2`.
    return log2_bits


def h2_bits(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def delta_d(alpha: float, t: float) -> float:
    lam = math.log2(3.0)
    sigma = lam + (alpha - 1.0) / t
    return alpha - sigma * t * h2_bits(1.0 / sigma), sigma


# ---------------------------------------------------------------- simulation

@njit
def _v2(x):
    v = 0
    while (x & 1) == 0:
        x >>= 1
        v += 1
    return v


@njit
def _step(n):
    x = 3 * n + 1
    return x >> _v2(x)


@njit(parallel=True)
def _survivors(N0, d, M):
    """Count of the M starts N0, N0+2, ... that survive d odd steps >= N0."""
    cnt = 0
    for k in prange(M):
        cur = N0 + 2 * k
        for _ in range(d):
            cur = _step(cur)
            if cur < N0:
                break
        else:
            cnt += 1
    return cnt


def empirical_survival(N0, d, M, threads=30):
    set_num_threads(threads)
    t0 = time.time()
    cnt = _survivors(N0, d, M)
    dt = time.time() - t0
    return cnt, M, dt


# -------------------------------------------------------------------- main

def main():
    out = {"partA": {}, "partB": {}, "meta": {}}
    out["meta"]["cpu"] = os.environ.get("PROCESSOR_IDENTIFIER", "?")
    out["meta"]["threads"] = 30

    # ---- Part A: I2 curve
    sigmas = [1.00, 1.05, 1.10, 4.0/3.0, 1.33, 1.40, math.log2(3.0), 1.60, 1.70, 1.80, 1.90, 2.00]
    a_table = []
    for s in sigmas:
        a_table.append({"sigma": round(s, 6), "I2_bits": round(i2_bits(s), 6)})
    out["partA"]["I2"] = a_table

    # c_star for a few (d, sigma)
    cs = []
    for d in (16, 32, 64, 128):
        for s in (4.0/3.0, math.log2(3.0), 1.33):
            cs.append({"d": d, "sigma": round(s, 6),
                       "c_star": round(2.0 ** (-d * i2_bits(s)), 8)})
    out["partA"]["c_star"] = cs

    # delta_d grid; find (alpha, t) reproducing paper delta_d ~ 0.5255
    dd_table = []
    lam = math.log2(3.0)
    for alpha in (1.10, 1.20, 1.30, 1.40, 1.50):
        tmin = (alpha - 1.0) / (2.0 - lam)
        tmax = 1.0 / lam
        for t in (tmin, tmax):
            dd, sigma = delta_d(alpha, t)
            dd_table.append({"alpha": alpha, "t": round(t, 6),
                             "sigma": round(sigma, 6), "delta_d": round(dd, 6)})
    out["partA"]["delta_d_grid"] = dd_table

    # ---- Part B: empirical one-block survival
    configs = [
        (2**16, 8,  2**18),
        (2**16, 16, 2**18),
        (2**16, 32, 2**18),
        (2**16, 64, 2**18),
        (2**20, 8,  2**18),
        (2**20, 16, 2**18),
        (2**20, 32, 2**18),
        (2**20, 64, 2**18),
    ]
    b_table = []
    for N0, d, M in configs:
        t0 = time.time()
        cnt, M, _ = empirical_survival(N0, d, M)
        elapsed = time.time() - t0
        frac = cnt / M
        # implied exponent per step (bits):  fraction = 2^(-d * rate)
        rate = 0.0 if frac <= 0 else (-math.log2(frac)) / d
        c_43 = 2.0 ** (-d * i2_bits(4.0/3.0))
        c_lam = 2.0 ** (-d * i2_bits(lam))
        b_table.append({
            "N0": N0, "d": d, "M": M,
            "survivors": cnt, "fraction": round(frac, 6),
            "implied_rate_bits/step": round(rate, 6),
            "c_star(4/3)": round(c_43, 6),
            "c_star(lambda)": round(c_lam, 6),
            "sec": round(elapsed, 2),
        })
        print(f"N0=2^{N0.bit_length()-1:<3} d={d:<4} frac={frac:.5f}  "
              f"rate={rate:.5f}  c*(4/3)={c_43:.5f}  c*(λ)={c_lam:.5f}  [{elapsed:.1f}s]")
    out["partB"]["one_block_survival"] = b_table

    # band check: at the paper's Gate-2 block scale (d ~ 8-16, N0 = 2^16)
    band_rows = [r for r in b_table if r["N0"] == 65536 and r["d"] <= 16]
    out["partB"]["gate2_band_check"] = {
        "rows": band_rows,
        "paper_band": [0.51, 0.56],
        "in_paper_band": all(0.51 <= r["fraction"] <= 0.56 for r in band_rows),
    }

    os.makedirs(os.path.join("..", "data"), exist_ok=True)
    import json
    p = os.path.join("..", "data", "route3_certificate.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nI2 curve:")
    for r in a_table:
        print(f"  sigma={r['sigma']:<7} I2={r['I2_bits']}")
    print(f"  -> certificate written: {p}")


if __name__ == "__main__":
    main()