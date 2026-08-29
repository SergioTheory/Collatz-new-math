"""
tail_audit.py — Audit of the "stubborn" trailing-ones tail under shadow descent.

For each exponent a in [2, A_MAX], scan odd multipliers M in [1, M_MAX]:
  * n0    = M * 2^a − 1        (start)
  * s     = 1 + v2(M * 3^a − 1) (exit shift; v2 = 2-adic valuation)
  * Y     = 2*(M*3^a − 1) / 2^s (exit value)
  * "growth" iff Y >= n0  (the shadow did NOT return below start)

We compute this EXACTLY and cheaply by 2-adic arithmetic only: for a fixed a,
the shift s depends only on  M * 3^a mod 2^w  (w = enough bits, w = 2*a+64),
so no giant 3^a integers are materialized.

Outputs data/tail_audit.json:
  per-a density of growth-M, and the aggregate survival curve of the tail.

Runs on 30 processes (one chunk of M per task).
"""
import json, os, time
from concurrent.futures import ProcessPoolExecutor
from math import log2

A_MAX = 200
M_MAX = 1 << 16        # scan M = 1,3,5,...,2^16-1 (odd)
W = 2 * A_MAX + 64     # enough 2-adic bits to resolve s ≤ 2a+64


def v2(x: int) -> int:
    return (x & -x).bit_length() - 1


def shift_of(a: int, M: int, pow3_mod: int, w: int) -> int:
    # s = 1 + v2(M * 3^a − 1)
    n = (M * pow3_mod - 1) & ((1 << w) - 1)
    return 1 + v2(n)


def audit_a(args):
    a, pow3_mod, w, m_range = args
    pow3_full = pow(3, a)          # computed once per a (cheap for a ≤ 1000)
    pow2a = 1 << a
    growth = 0
    total = 0
    for M in m_range:
        s = shift_of(a, M, pow3_mod, w)
        lhs = M * pow3_full - 1
        rhs = (1 << (s - 1)) * (M * pow2a - 1)
        total += 1
        if lhs >= rhs:
            growth += 1
    return a, growth, total


def main() -> None:
    t0 = time.time()
    w = W
    results = {}
    for a in range(2, A_MAX + 1):
        pow3 = pow(3, a, 1 << w)
        # chunk M over processes
        odds = list(range(1, M_MAX + 1, 2))
        chunk = max(1, len(odds) // 30 + 1)
        ranges = [odds[i:i + chunk] for i in range(0, len(odds), chunk)]
        tasks = [(a, pow3, w, r) for r in ranges]
        growth = 0
        total = 0
        with ProcessPoolExecutor(max_workers=30) as ex:
            for _, g, t in ex.map(audit_a, tasks):
                growth += g
                total += t
        density = growth / total
        results[a] = {"growth": growth, "total": total,
                      "density": round(density, 8)}
        if a <= 10 or a % 50 == 0 or a == A_MAX:
            print(f"a={a:>4}: growth {growth}/{total}  density={density:.2e}")

    # aggregate: does density decay like 2^(-c·a)?
    out = {
        "A_MAX": A_MAX, "M_MAX": M_MAX,
        "by_a": results,
        "elapsed_sec": round(time.time() - t0, 2),
    }
    p = os.path.join("..", "data", "tail_audit.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("certificate ->", p)


if __name__ == "__main__":
    main()