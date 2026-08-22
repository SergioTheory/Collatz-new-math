
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
for p in (ROOT_DIR, DIST_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Optional project helpers
HAVE_PROJECT_HELPERS = False
collatz_peak = None
analyze_to_peak = None
number_from_parity = None

for modname in ("crt_solver", "dist.crt_solver"):
    try:
        mod = __import__(modname, fromlist=["collatz_peak", "analyze_to_peak", "number_from_parity"])
        collatz_peak = getattr(mod, "collatz_peak", None)
        analyze_to_peak = getattr(mod, "analyze_to_peak", None)
        number_from_parity = getattr(mod, "number_from_parity", None)
        HAVE_PROJECT_HELPERS = True
        break
    except Exception:
        pass

try:
    import sympy  # type: ignore
    HAVE_SYMPY = True
except Exception:
    HAVE_SYMPY = False

LOG2_3 = math.log2(3.0)
SMOOTH_BOUND_DEFAULT = 100

PRIMARY_CENTERS: Dict[int, Dict[str, Any]] = {
    14:  {"center": 719,                        "center_bits": 10, "hit_rate": 0.805, "inputs": 33,  "status": "CONFIRMED"},
    16:  {"center": 6803,                       "center_bits": 13, "hit_rate": 0.846, "inputs": 22,  "status": "CONFIRMED"},
    18:  {"center": 27611,                      "center_bits": 15, "hit_rate": 0.862, "inputs": 25,  "status": "CONFIRMED"},
    19:  {"center": 15977,                      "center_bits": 14, "hit_rate": 0.722, "inputs": 39,  "status": "CANDIDATE"},
    21:  {"center": 52487,                      "center_bits": 16, "hit_rate": 0.771, "inputs": 37,  "status": "CANDIDATE"},
    22:  {"center": 61823,                      "center_bits": 16, "hit_rate": 0.743, "inputs": 55,  "status": "CANDIDATE"},
    23:  {"center": 41471,                      "center_bits": 16, "hit_rate": 0.825, "inputs": 104, "status": "CONFIRMED"},
    24:  {"center": 586115,                     "center_bits": 20, "hit_rate": 0.821, "inputs": 32,  "status": "CONFIRMED"},
    25:  {"center": 705307,                     "center_bits": 20, "hit_rate": 0.778, "inputs": 28,  "status": "CANDIDATE"},
    26:  {"center": 1085723,                    "center_bits": 21, "hit_rate": 0.754, "inputs": 52,  "status": "CANDIDATE"},
    27:  {"center": 4918427,                    "center_bits": 23, "hit_rate": 0.818, "inputs": 36,  "status": "CONFIRMED"},
    30:  {"center": 58595471,                   "center_bits": 26, "hit_rate": 0.816, "inputs": 31,  "status": "CONFIRMED"},
    140: {"center": 20152090995747160937051,    "center_bits": 75, "hit_rate": 1.000, "inputs": 913, "status": "CONFIRMED"},
}
ALT_CENTERS: Dict[int, Dict[str, Any]] = {
    14: {"center": 121,     "center_bits": 7,  "status": "KNOWN_PREDECESSOR"},
    18: {"center": 10151,   "center_bits": 14, "status": "CENSUS_ALTERNATIVE"},
    27: {"center": 5808671, "center_bits": 23, "status": "KNOWN_PREDECESSOR"},
}

MODULI = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 32, 48, 64, 128, 256]
SMALL_PRIMES = []

def sieve_primes(limit: int = 10000) -> List[int]:
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i:limit+1:i] = b"\x00" * (((limit - i*i) // i) + 1)
    return [i for i, f in enumerate(sieve) if f]

SMALL_PRIMES = sieve_primes(10000)

def v2(n: int) -> int:
    if n == 0:
        return 0
    c = 0
    while n % 2 == 0:
        n //= 2
        c += 1
    return c

def popcount(n: int) -> int:
    return n.bit_count()

def max_run(s: str, ch: str) -> int:
    best = cur = 0
    for x in s:
        if x == ch:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best

def fmt_int(n: Any, width: int = 0) -> str:
    s = str(n)
    return s.rjust(width) if width else s

def pretty_int(n: int, max_len: int = 22) -> str:
    s = str(n)
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return f"{s[:half]}…{s[-half:]}"

def format_factorization(f: Dict[int, int]) -> str:
    if not f:
        return "1"
    parts = []
    for p in sorted(f):
        e = f[p]
        parts.append(f"{p}^{e}" if e != 1 else str(p))
    return " × ".join(parts)

def is_prime_power(f: Dict[int, int]) -> bool:
    return len(f) == 1

def is_semiprime(f: Dict[int, int]) -> bool:
    return sum(f.values()) == 2

def is_smooth(f: Dict[int, int], bound: int = SMOOTH_BOUND_DEFAULT) -> bool:
    return all(p <= bound for p in f) if f else True

def nearest_pow2_info(n: int) -> Tuple[int, int]:
    if n <= 0:
        return 0, 0
    k = max(0, round(math.log2(n)))
    best_k = k
    best_d = abs(n - (1 << k))
    for kk in (k - 1, k + 1):
        if kk >= 0:
            d = abs(n - (1 << kk))
            if d < best_d:
                best_k, best_d = kk, d
    return best_k, best_d

def nearest_repunit_info(n: int) -> Tuple[int, int]:
    if n < 0:
        return 0, 0
    k = max(1, round(math.log2(n + 1)))
    best_k = k
    best_d = abs(n - ((1 << k) - 1))
    for kk in (k - 1, k + 1):
        if kk >= 1:
            d = abs(n - ((1 << kk) - 1))
            if d < best_d:
                best_k, best_d = kk, d
    return best_k, best_d

def _is_probable_prime(n: int, rounds: int = 10) -> bool:
    if n < 2:
        return False
    for p in SMALL_PRIMES[:250]:
        if n == p:
            return True
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2
    bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    rng = random.SystemRandom()
    for i in range(rounds):
        a = bases[i] if i < len(bases) else rng.randrange(2, n - 2)
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True

def _pollard_rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
    rng = random.SystemRandom()
    while True:
        c = rng.randrange(1, n - 1)
        x = rng.randrange(0, n - 1)
        y = x
        d = 1
        def f(v: int) -> int:
            return (v * v + c) % n
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d

@lru_cache(maxsize=None)
def factorint_cached(n: int) -> Tuple[Tuple[int, int], ...]:
    n = abs(int(n))
    if n in (0, 1):
        return tuple()
    factors: Dict[int, int] = defaultdict(int)
    def factor(x: int) -> None:
        if x == 1:
            return
        if _is_probable_prime(x):
            factors[x] += 1
            return
        for p in SMALL_PRIMES[:500]:
            if p * p > x:
                break
            if x % p == 0:
                e = 0
                while x % p == 0:
                    x //= p
                    e += 1
                factors[p] += e
                if x == 1:
                    return
                if _is_probable_prime(x):
                    factors[x] += 1
                    return
        if x == 1:
            return
        if _is_probable_prime(x):
            factors[x] += 1
            return
        d = _pollard_rho(x)
        if d in (1, x):
            factors[x] += 1
            return
        factor(d)
        factor(x // d)
    factor(n)
    return tuple(sorted(factors.items()))

def factorint_best_effort(n: int) -> Dict[int, int]:
    if n in (0, 1):
        return {}
    if HAVE_SYMPY:
        try:
            return dict(sorted((int(p), int(e)) for p, e in sympy.factorint(int(n)).items()))  # type: ignore
        except Exception:
            pass
    return dict(factorint_cached(n))

def odd_shift_trajectory(n: int, limit: int = 100000) -> Tuple[List[int], List[int]]:
    if n <= 0:
        raise ValueError("n must be positive")
    x = n
    while x % 2 == 0:
        x //= 2
    shifts = []
    odd_terms = [x]
    while x != 1 and len(shifts) < limit:
        a = v2(3 * x + 1)
        shifts.append(a)
        x = (3 * x + 1) >> a
        odd_terms.append(x)
    return shifts, odd_terms

def collatz_full_trajectory(n: int, limit: int = 200000) -> List[int]:
    if n <= 0:
        raise ValueError("n must be positive")
    x = n
    traj = [x]
    while x != 1 and len(traj) < limit:
        x = 3 * x + 1 if x & 1 else x >> 1
        traj.append(x)
    return traj

def analyze_center(n: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {"center": n}
    if analyze_to_peak is not None:
        try:
            proj = analyze_to_peak(n)
            if isinstance(proj, dict):
                out["project"] = proj
        except Exception as exc:
            out["project_error"] = repr(exc)
    traj = collatz_full_trajectory(n)
    peak_step = max(range(len(traj)), key=lambda i: traj[i])
    peak_value = traj[peak_step]
    shifts, odd_terms = odd_shift_trajectory(n)
    out["full_trajectory"] = traj
    out["full_peak_step"] = peak_step
    out["full_peak_value"] = peak_value
    out["full_peak_bits"] = peak_value.bit_length()
    out["odd_shifts"] = shifts
    out["odd_terms"] = odd_terms
    out["odd_steps"] = len(shifts)
    out["odd_S"] = sum(shifts)
    out["odd_gain"] = len(shifts) * LOG2_3 - sum(shifts)
    out["odd_S_over_d"] = (sum(shifts) / len(shifts)) if shifts else None
    out["odd_peak_value"] = max(odd_terms)
    out["odd_peak_bits"] = max(odd_terms).bit_length()
    return out

def pre_peak_hit(traj: List[int], target: int, peak_step: int) -> Optional[int]:
    stop = min(peak_step, len(traj))
    try:
        return traj[:stop].index(target)
    except ValueError:
        return None

def trajectory_relation(rec_a: Dict[str, Any], rec_b: Dict[str, Any]) -> Dict[str, Any]:
    traj_a = rec_a["analysis"]["full_trajectory"]
    traj_b = rec_b["analysis"]["full_trajectory"]
    peak_a = rec_a["analysis"]["full_peak_step"]
    peak_b = rec_b["analysis"]["full_peak_step"]
    idx_a_b = pre_peak_hit(traj_a, rec_b["center"], peak_a)
    idx_b_a = pre_peak_hit(traj_b, rec_a["center"], peak_b)
    set_b = set(traj_b)
    common = None
    a_idx = b_idx = None
    for i, x in enumerate(traj_a):
        if x in set_b:
            common = x
            a_idx = i
            b_idx = traj_b.index(x)
            break
    return {
        "a_hits_b_before_peak": idx_a_b is not None,
        "a_hits_b_step": idx_a_b,
        "b_hits_a_before_peak": idx_b_a is not None,
        "b_hits_a_step": idx_b_a,
        "first_common_value": common,
        "first_common_value_a_step": a_idx,
        "first_common_value_b_step": b_idx,
    }

def continued_fraction_convergents_from_float(x: float, max_terms: int = 20) -> List[Fraction]:
    terms = []
    y = x
    for _ in range(max_terms):
        a = int(math.floor(y))
        terms.append(a)
        frac = y - a
        if abs(frac) < 1e-15:
            break
        y = 1.0 / frac
    p_prev, p = 1, terms[0]
    q_prev, q = 0, 1
    convs = [Fraction(p, q)]
    for a in terms[1:]:
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
        convs.append(Fraction(p, q))
    return convs

CF_LOG2_3 = continued_fraction_convergents_from_float(LOG2_3, 20)

def nearest_convergent(frac: Fraction, convs: List[Fraction]) -> Fraction:
    best = convs[0]
    best_d = abs(frac - best)
    for c in convs[1:]:
        d = abs(frac - c)
        if d < best_d:
            best = c
            best_d = d
    return best

def resonance_search(center: int, k_max: int, m_max: int, window: int = 4, top_n: int = 8) -> Dict[str, Any]:
    pow3 = [1]
    for _ in range(k_max):
        pow3.append(pow3[-1] * 3)
    log2_center = math.log2(center)
    top: List[Dict[str, Any]] = []
    best: Optional[Dict[str, Any]] = None
    for k in range(1, k_max + 1):
        m_est = int(round(k * LOG2_3 - log2_center))
        lo = max(1, m_est - window)
        hi = min(m_max, m_est + window)
        target3 = pow3[k]
        for m in range(lo, hi + 1):
            diff = abs(center * (1 << m) - target3)
            rel = diff / target3
            item = {
                "k": k,
                "m": m,
                "abs_error": int(diff),
                "rel_error": float(rel),
                "ratio_m_over_k": m / k,
                "delta_to_log2_3": (m / k) - LOG2_3,
                "target3": int(target3),
            }
            if best is None or diff * best["target3"] < best["abs_error"] * target3:
                best = item.copy()
            top.append(item)
            top.sort(key=lambda d: (d["rel_error"], d["abs_error"]))
            top = top[:top_n]
    if best is None:
        best = {"k": None, "m": None, "abs_error": None, "rel_error": None, "ratio_m_over_k": None, "delta_to_log2_3": None, "target3": None}
    best["nearest_convergent_m_over_k"] = str(nearest_convergent(Fraction(best["m"], best["k"]), CF_LOG2_3)) if best["k"] and best["m"] else None
    return {"best": best, "top": top}

def make_specs() -> List[Dict[str, Any]]:
    out = []
    for peak, info in PRIMARY_CENTERS.items():
        out.append({
            "peak": peak,
            "center": int(info["center"]),
            "expected_bits": int(info.get("center_bits")) if info.get("center_bits") is not None else None,
            "hit_rate": info.get("hit_rate"),
            "inputs": info.get("inputs"),
            "status": info.get("status", "UNKNOWN"),
            "kind": "primary",
            "label": "primary",
        })
    for peak, info in ALT_CENTERS.items():
        out.append({
            "peak": peak,
            "center": int(info["center"]),
            "expected_bits": int(info.get("center_bits")) if info.get("center_bits") is not None else None,
            "hit_rate": None,
            "inputs": None,
            "status": info.get("status", "UNKNOWN"),
            "kind": "alt",
            "label": "alt",
        })
    return out

def analyze_spec(spec: Dict[str, Any], smooth_bound: int, k_max: int, m_max: int, xk_max: int, xm_max: int) -> Dict[str, Any]:
    c = int(spec["center"])
    bits_actual = c.bit_length()
    fac = factorint_best_effort(c)
    fac_m1 = factorint_best_effort(max(1, c - 1))
    fac_p1 = factorint_best_effort(c + 1)
    fac_3c1 = factorint_best_effort(3 * c + 1)
    odd_an = analyze_center(c)
    res = resonance_search(c, xk_max, xm_max, window=4, top_n=8) if c == PRIMARY_CENTERS[140]["center"] else resonance_search(c, k_max, m_max, window=4, top_n=8)
    result = {
        "peak": spec["peak"],
        "center": c,
        "center_str": str(c),
        "center_bits_expected": spec["expected_bits"],
        "center_bits_actual": bits_actual,
        "hit_rate": spec["hit_rate"],
        "inputs": spec["inputs"],
        "status": spec["status"],
        "kind": spec["kind"],
        "label": spec["label"],
        "factorization": {
            "c": {
                "string": format_factorization(fac),
                "factors": {str(p): e for p, e in fac.items()},
                "num_divisors": math.prod((e + 1) for e in fac.values()) if fac else 1,
                "prime": len(fac) == 1 and list(fac.values())[0] == 1 if fac else False,
                "prime_power": is_prime_power(fac),
                "semiprime": is_semiprime(fac),
                "smooth": is_smooth(fac, smooth_bound),
            },
            "c_minus_1": {"string": format_factorization(fac_m1), "factors": {str(p): e for p, e in fac_m1.items()}},
            "c_plus_1": {"string": format_factorization(fac_p1), "factors": {str(p): e for p, e in fac_p1.items()}},
            "three_c_plus_1": {"string": format_factorization(fac_3c1), "factors": {str(p): e for p, e in fac_3c1.items()}, "v2": v2(3 * c + 1)},
        },
        "modular": {str(m): c % m for m in MODULI},
        "binary": {
            "bin": bin(c)[2:],
            "bits": bits_actual,
            "popcount": popcount(c),
            "density": popcount(c) / bits_actual,
            "max_run_ones": max_run(bin(c)[2:], "1"),
            "max_run_zeros": max_run(bin(c)[2:], "0"),
            "prefix8": bin(c)[2:][:8],
            "suffix8": bin(c)[2:][-8:],
            "nearest_pow2_k": nearest_pow2_info(c)[0],
            "nearest_pow2_dist": nearest_pow2_info(c)[1],
            "nearest_2k_minus_1_k": nearest_repunit_info(c)[0],
            "nearest_2k_minus_1_dist": nearest_repunit_info(c)[1],
        },
        "analysis": odd_an,
        "resonance": res,
    }
    d = odd_an["odd_steps"]
    S = odd_an["odd_S"]
    if d > 0:
        result["analysis"]["S_over_d"] = S / d
        result["analysis"]["delta_to_log2_3"] = LOG2_3 - (S / d)
        result["analysis"]["nearest_convergent_S_over_d"] = str(nearest_convergent(Fraction(S, d), CF_LOG2_3))
    else:
        result["analysis"]["S_over_d"] = None
        result["analysis"]["delta_to_log2_3"] = None
        result["analysis"]["nearest_convergent_S_over_d"] = None
    # Expected bits if available are just metadata, not fit input.
    result["peak_bits_actual"] = odd_an["full_peak_bits"]
    result["peak_value_actual"] = odd_an["full_peak_value"]
    return result

def add_prepeak_hits(records: List[Dict[str, Any]]) -> None:
    centers = [r["center"] for r in records]
    for rec in records:
        traj = rec["analysis"]["full_trajectory"]
        peak_step = rec["analysis"]["full_peak_step"]
        hits = []
        for t in centers:
            if t == rec["center"]:
                continue
            idx = pre_peak_hit(traj, t, peak_step)
            if idx is not None:
                hits.append({"target": t, "step": idx})
        rec["pre_peak_hits"] = hits
        rec["pre_peak_hits_count"] = len(hits)

def compare_same_peak_groups(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_peak = defaultdict(list)
    for r in records:
        by_peak[r["peak"]].append(r)
    out = []
    for peak, grp in sorted(by_peak.items()):
        if len(grp) < 2:
            continue
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                a, b = grp[i], grp[j]
                out.append({
                    "peak": peak,
                    "a": {"kind": a["kind"], "center": a["center"], "status": a["status"]},
                    "b": {"kind": b["kind"], "center": b["center"], "status": b["status"]},
                    "relation": trajectory_relation(a, b),
                })
    return out

def linear_regression(xs: List[float], ys: List[float]) -> Dict[str, float]:
    n = len(xs)
    if n == 0 or len(ys) != n:
        raise ValueError("bad regression data")
    xm = sum(xs) / n
    ym = sum(ys) / n
    cov = sum((x - xm) * (y - ym) for x, y in zip(xs, ys))
    varx = sum((x - xm) ** 2 for x in xs)
    vary = sum((y - ym) ** 2 for y in ys)
    slope = cov / varx if varx else 0.0
    intercept = ym - slope * xm
    yhat = [slope * x + intercept for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, yhat))
    r2 = 1.0 - ss_res / vary if vary else 1.0
    return {"slope": slope, "intercept": intercept, "r2": r2}

def fit_models(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Use actual computed bits; never rely on input metadata.
    xs = [r["peak"] for r in records]
    centers = [r["center"] for r in records]
    bits = [r["center_bits_actual"] for r in records]

    # Exclude x* from generic fits because it is an extreme outlier.
    base = [r for r in records if r["peak"] != 140]
    xs_b = [r["peak"] for r in base]
    centers_b = [r["center"] for r in base]
    bits_b = [r["center_bits_actual"] for r in base]

    fit_log_center = linear_regression(xs_b, [math.log(c) for c in centers_b])
    fit_bits = linear_regression(xs_b, bits_b)
    fit_loglog = linear_regression([math.log(p) for p in xs_b], [math.log(c) for c in centers_b])

    def pred_center(p: int) -> float:
        return math.exp(fit_log_center["intercept"] + fit_log_center["slope"] * p)

    def pred_bits(p: int) -> float:
        return fit_bits["intercept"] + fit_bits["slope"] * p

    return {
        "fit_log_center_vs_peak": fit_log_center,
        "fit_bits_vs_peak": fit_bits,
        "fit_log_center_vs_log_peak": fit_loglog,
        "predictions": {
            "peak_30_center": pred_center(30),
            "peak_35_center": pred_center(35),
            "peak_50_center": pred_center(50),
            "peak_140_center": pred_center(140),
            "peak_30_bits": pred_bits(30),
            "peak_35_bits": pred_bits(35),
            "peak_50_bits": pred_bits(50),
            "peak_140_bits": pred_bits(140),
        },
    }

def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    primary = [r for r in records if r["kind"] == "primary"]
    counts = Counter(r["status"] for r in primary)
    return {
        "n_records": len(records),
        "n_primary": len(primary),
        "n_alt": len(records) - len(primary),
        "counts_primary": dict(counts),
        "confirmed_peaks": [r["peak"] for r in primary if r["status"] == "CONFIRMED"],
        "candidate_peaks": [r["peak"] for r in primary if r["status"] == "CANDIDATE"],
        "none_peaks": [r["peak"] for r in primary if r["status"] == "NONE"],
    }

def to_jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [to_jsonable(v) for v in x]
    if isinstance(x, tuple):
        return [to_jsonable(v) for v in x]
    if isinstance(x, Fraction):
        return f"{x.numerator}/{x.denominator}"
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    return str(x)

def write_csv(path: str, records: List[Dict[str, Any]], fit: Dict[str, Any]) -> None:
    fields = [
        "peak", "kind", "center", "center_bits_actual", "center_bits_expected", "status", "hit_rate", "inputs",
        "prime", "prime_power", "semiprime", "smooth", "v2_3c_plus_1",
        "full_peak_bits", "full_peak_value", "full_peak_step",
        "odd_steps", "odd_S", "odd_S_over_d", "pre_peak_hits_count",
        "res_best_k", "res_best_m", "res_rel_error", "res_ratio_mk",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rec in records:
            fac = rec["factorization"]["c"]
            res = rec["resonance"]["best"]
            row = {
                "peak": rec["peak"],
                "kind": rec["kind"],
                "center": rec["center"],
                "center_bits_actual": rec["center_bits_actual"],
                "center_bits_expected": rec["center_bits_expected"],
                "status": rec["status"],
                "hit_rate": rec["hit_rate"],
                "inputs": rec["inputs"],
                "prime": fac["prime"],
                "prime_power": fac["prime_power"],
                "semiprime": fac["semiprime"],
                "smooth": fac["smooth"],
                "v2_3c_plus_1": rec["factorization"]["three_c_plus_1"]["v2"],
                "full_peak_bits": rec["peak_bits_actual"],
                "full_peak_value": rec["peak_value_actual"],
                "full_peak_step": rec["analysis"]["full_peak_step"],
                "odd_steps": rec["analysis"]["odd_steps"],
                "odd_S": rec["analysis"]["odd_S"],
                "odd_S_over_d": rec["analysis"]["S_over_d"],
                "pre_peak_hits_count": rec.get("pre_peak_hits_count", 0),
                "res_best_k": res["k"],
                "res_best_m": res["m"],
                "res_rel_error": res["rel_error"],
                "res_ratio_mk": res["ratio_m_over_k"],
            }
            w.writerow(row)

def print_section(title: str) -> None:
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)

def row(vals: List[Any], widths: List[int]) -> str:
    return "  " + "  ".join(str(v).rjust(w) for v, w in zip(vals, widths))

def report(records: List[Dict[str, Any]], fit: Dict[str, Any]) -> None:
    print_section("Algebraic Anatomy of Confluence Centers")
    print(f"  Project helpers: {'yes' if HAVE_PROJECT_HELPERS else 'no'}")
    print(f"  sympy factorization: {'yes' if HAVE_SYMPY else 'no'}")
    print(f"  Records: {len(records)}")
    print(f"  Primary records: {sum(1 for r in records if r['kind'] == 'primary')}")
    print(f"  Alt records: {sum(1 for r in records if r['kind'] == 'alt')}")
    print()

    print_section("A. FACTORIZATION")
    hdr = ["Center", "Bits", "Factorization", "Prime?", "Pwr?", "Semi?", "Smooth?", "v2(3c+1)"]
    wds = [22, 6, 34, 7, 6, 6, 8, 9]
    print(row(hdr, wds))
    print("  " + "-" * 120)
    for rec in records:
        fac = rec["factorization"]["c"]
        print(row([
            pretty_int(rec["center"], 22),
            rec["center_bits_actual"],
            fac["string"],
            "yes" if fac["prime"] else "no",
            "yes" if fac["prime_power"] else "no",
            "yes" if fac["semiprime"] else "no",
            "yes" if fac["smooth"] else "no",
            rec["factorization"]["three_c_plus_1"]["v2"],
        ], wds))

    print_section("B. MODULAR PATTERNS")
    mods_show = [3, 8, 16, 32, 64, 128, 256]
    hdr = ["Center"] + [f"mod{m}" for m in mods_show]
    wds = [22] + [8] * len(mods_show)
    print(row(hdr, wds))
    print("  " + "-" * 110)
    for rec in records:
        print(row([pretty_int(rec["center"], 22)] + [rec["modular"][str(m)] for m in mods_show], wds))

    print("\n  Shared residues:")
    for m in mods_show:
        vals = [rec["modular"][str(m)] for rec in records]
        if all(v == vals[0] for v in vals):
            print(f"    mod {m}: all equal to {vals[0]}")
        else:
            cnt = Counter(vals)
            res, freq = cnt.most_common(1)[0]
            print(f"    mod {m}: mixed, most common={res} ({freq}/{len(vals)})")

    print_section("C. BINARY STRUCTURE")
    hdr = ["Center", "Bits", "Density", "Max1", "Max0", "Prefix8", "Suffix8"]
    wds = [22, 6, 8, 6, 6, 10, 10]
    print(row(hdr, wds))
    print("  " + "-" * 90)
    for rec in records:
        b = rec["binary"]
        print(row([
            pretty_int(rec["center"], 22), b["bits"], f"{b['density']:.4f}", b["max_run_ones"], b["max_run_zeros"], b["prefix8"], b["suffix8"]
        ], wds))

    print_section("D. NEAREST 3^k / 2^m")
    hdr = ["Center", "k", "m", "RelErr", "m/k", "m/k-log2(3)", "Conv"]
    wds = [22, 6, 6, 12, 10, 14, 12]
    print(row(hdr, wds))
    print("  " + "-" * 100)
    for rec in records:
        best = rec["resonance"]["best"]
        print(row([
            pretty_int(rec["center"], 22),
            best["k"] if best["k"] is not None else "—",
            best["m"] if best["m"] is not None else "—",
            f"{best['rel_error']:.6e}" if best["rel_error"] is not None else "—",
            f"{best['ratio_m_over_k']:.6f}" if best["ratio_m_over_k"] is not None else "—",
            f"{best['delta_to_log2_3']:.6f}" if best["delta_to_log2_3"] is not None else "—",
            best.get("nearest_convergent_m_over_k", "—"),
        ], wds))

    print_section("E. TRAJECTORY FROM CENTER")
    hdr = ["Peak", "Center", "PeakBits", "PeakValue", "PeakStep", "d", "S", "S/d", "Conv"]
    wds = [6, 22, 8, 18, 8, 8, 8, 10, 12]
    print(row(hdr, wds))
    print("  " + "-" * 120)
    for rec in records:
        an = rec["analysis"]
        print(row([
            rec["peak"], pretty_int(rec["center"], 22), rec["peak_bits_actual"], pretty_int(rec["peak_value_actual"], 18), an["full_peak_step"],
            an["odd_steps"], an["odd_S"], f"{an['S_over_d']:.6f}" if an["S_over_d"] is not None else "—",
            an["nearest_convergent_S_over_d"] or "—"
        ], wds))

    print("\n  Pre-peak hits:")
    for rec in records:
        hits = rec.get("pre_peak_hits", [])
        if hits:
            txt = ", ".join(f"{h['target']}@{h['step']}" for h in hits[:6])
            if len(hits) > 6:
                txt += f", ... (+{len(hits)-6})"
            print(f"    {pretty_int(rec['center'], 22)}: {txt}")

    print_section("F. GROWTH FIT")
    fl = fit["fit_log_center_vs_peak"]
    fb = fit["fit_bits_vs_peak"]
    fp = fit["fit_log_center_vs_log_peak"]
    A = math.exp(fl["intercept"])
    B = math.exp(fl["slope"])
    print(f"  center ≈ A * B^peak")
    print(f"    A = {A:.6e}")
    print(f"    B = {B:.12f}")
    print(f"    R² = {fl['r2']:.6f}")
    print(f"  center_bits ≈ α*peak + β")
    print(f"    α = {fb['slope']:.12f}")
    print(f"    β = {fb['intercept']:.12f}")
    print(f"    R² = {fb['r2']:.6f}")
    print(f"  log(center) ≈ a + b*log(peak)")
    print(f"    a = {fp['intercept']:.12f}")
    print(f"    b = {fp['slope']:.12f}")
    print(f"    R² = {fp['r2']:.6f}")
    print("  Predictions:")
    for p in (30, 35, 50, 140):
        print(f"    peak={p}: center≈{fit['predictions'][f'peak_{p}_center']:.6e}, bits≈{fit['predictions'][f'peak_{p}_bits']:.3f}")
    print("  Hold-out sanity:")
    print(f"    peak=30 actual={PRIMARY_CENTERS[30]['center']}")
    print(f"    peak=140 actual={PRIMARY_CENTERS[140]['center']}")

    print_section("G. CONTINUED FRACTION CONNECTION")
    hdr = ["Peak", "Center", "d", "S", "S/d", "Nearest conv", "δ"]
    wds = [6, 22, 8, 8, 10, 12, 12]
    print(row(hdr, wds))
    print("  " + "-" * 100)
    for rec in records:
        an = rec["analysis"]
        print(row([
            rec["peak"], pretty_int(rec["center"], 22), an["odd_steps"], an["odd_S"],
            f"{an['S_over_d']:.6f}" if an["S_over_d"] is not None else "—",
            an["nearest_convergent_S_over_d"] or "—",
            f"{an['delta_to_log2_3']:.6f}" if an["delta_to_log2_3"] is not None else "—",
        ], wds))

    print_section("H. CRT / RESIDUE SUMMARY")
    hdr = ["Peak", "Center", "v2(3c+1)", "S used", "mod 2^S example", "Comment"]
    wds = [6, 22, 10, 8, 16, 24]
    print(row(hdr, wds))
    print("  " + "-" * 100)
    for rec in records:
        S = rec["analysis"]["odd_S"]
        mod = rec["center"] % (1 << S) if S is not None and S < 1024 else (rec["center"] % (1 << 20) if S else 0)
        print(row([
            rec["peak"], pretty_int(rec["center"], 22), rec["factorization"]["three_c_plus_1"]["v2"],
            S if S is not None else "—", mod, "odd-trajectory residue"
        ], wds))

    print_section("I. FORMULA CANDIDATES")
    print(f"  Candidate 1: center ≈ {A:.6e} * ({B:.12f})^peak   (R²={fl['r2']:.6f})")
    print(f"  Candidate 2: center_bits ≈ {fb['slope']:.12f} * peak + {fb['intercept']:.12f}   (R²={fb['r2']:.6f})")
    print(f"  Candidate 3: log(center) ≈ {fp['intercept']:.12f} + {fp['slope']:.12f} * log(peak)   (R²={fp['r2']:.6f})")
    print("  Top resonance examples:")
    for rec in records[:5]:
        top = rec["resonance"]["top"][:3]
        txt = " ; ".join(f"(k={t['k']},m={t['m']},rel={t['rel_error']:.3e})" for t in top)
        print(f"    {pretty_int(rec['center'], 22)}: {txt}")

    same_peak = compare_same_peak_groups(records)
    if same_peak:
        print_section("J. SAME-PEAK RELATIONS")
        for rel in same_peak:
            a = rel["a"]; b = rel["b"]; rr = rel["relation"]
            print(
                f"  peak={rel['peak']}: {a['kind']} {pretty_int(a['center'], 12)} ↔ {b['kind']} {pretty_int(b['center'], 12)} | "
                f"A hits B before peak={rr['a_hits_b_before_peak']} step={rr['a_hits_b_step']} | "
                f"B hits A before peak={rr['b_hits_a_before_peak']} step={rr['b_hits_a_step']} | "
                f"first common={rr['first_common_value']}"
            )

    print_section("SUMMARY")
    primary = [r for r in records if r["kind"] == "primary"]
    counts = Counter(r["status"] for r in primary)
    print(f"  Primary counts: {dict(counts)}")
    print(f"  Confirmed peaks: {[r['peak'] for r in primary if r['status']=='CONFIRMED']}")
    print(f"  Candidate peaks: {[r['peak'] for r in primary if r['status']=='CANDIDATE']}")
    print(f"  None peaks: {[r['peak'] for r in primary if r['status']=='NONE']}")
    print(f"  Elapsed: {time.time() - START_TIME:.2f}s")

def main() -> None:
    global START_TIME
    START_TIME = time.time()
    p = argparse.ArgumentParser(description="Algebraic Anatomy of Confluence Centers")
    p.add_argument("--json", default="algebra_centers.json")
    p.add_argument("--csv", default="algebra_centers.csv")
    p.add_argument("--workers", type=int, default=0)
    p.add_argument("--no-parallel", action="store_true")
    p.add_argument("--smooth-bound", type=int, default=SMOOTH_BOUND_DEFAULT)
    p.add_argument("--k-max", type=int, default=300)
    p.add_argument("--m-max", type=int, default=500)
    p.add_argument("--xstar-k-max", type=int, default=500)
    p.add_argument("--xstar-m-max", type=int, default=800)
    args = p.parse_args()

    specs = make_specs()
    if args.no_parallel:
        workers = 1
    else:
        workers = args.workers if args.workers > 0 else min(8, os.cpu_count() or 1, len(specs))
        workers = max(1, workers)

    print_section("Algebraic Anatomy of Confluence Centers")
    print(f"  Project helpers: {'yes' if HAVE_PROJECT_HELPERS else 'no'}")
    print(f"  sympy factorization: {'yes' if HAVE_SYMPY else 'no'}")
    print(f"  Workers: {workers}")
    print(f"  Smooth bound: {args.smooth_bound}")
    print(f"  Resonance scan ordinary: k<= {args.k_max}, m<= {args.m_max}")
    print(f"  Resonance scan x*: k<= {args.xstar_k_max}, m<= {args.xstar_m_max}")

    records: List[Dict[str, Any]] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(analyze_spec, s, args.smooth_bound, args.k_max, args.m_max, args.xstar_k_max, args.xstar_m_max) for s in specs]
            for f in futs:
                records.append(f.result())
    else:
        for s in specs:
            records.append(analyze_spec(s, args.smooth_bound, args.k_max, args.m_max, args.xstar_k_max, args.xstar_m_max))

    records.sort(key=lambda r: (r["peak"], 0 if r["kind"] == "primary" else 1, r["center"]))
    add_prepeak_hits(records)
    fit = fit_models([r for r in records if r["kind"] == "primary"])
    report(records, fit)

    out = {
        "metadata": {
            "project_helpers": HAVE_PROJECT_HELPERS,
            "sympy": HAVE_SYMPY,
            "workers": workers,
            "smooth_bound": args.smooth_bound,
            "k_max": args.k_max,
            "m_max": args.m_max,
            "xstar_k_max": args.xstar_k_max,
            "xstar_m_max": args.xstar_m_max,
            "elapsed_seconds": time.time() - START_TIME,
            "log2_3": LOG2_3,
            "continued_fraction_log2_3": [f"{f.numerator}/{f.denominator}" for f in CF_LOG2_3],
        },
        "records": records,
        "summary": summarize(records),
        "fits": fit,
        "same_peak_relations": compare_same_peak_groups(records),
        "primary_centers": PRIMARY_CENTERS,
        "alt_centers": ALT_CENTERS,
    }

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(to_jsonable(out), f, ensure_ascii=False, indent=2)
    write_csv(args.csv, records, fit)
    print("\n" + "=" * 90)
    print(f"  JSON saved: {args.json}")
    print(f"  CSV saved:  {args.csv}")
    print("=" * 90)

if __name__ == "__main__":
    try:
        from multiprocessing import freeze_support
        freeze_support()
    except Exception:
        pass
    main()
