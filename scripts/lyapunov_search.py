"""
lyapunov_search.py — Search for periodic Lyapunov weights for Collatz.

For V(n) = n · w[n mod 2^k], solves LP for optimal weights w
such that V(Syr^d(n)) <= c* · V(n) with minimum c*.

If c* < 1: BREAKTHROUGH — Collatz conjecture reduced to finite verification!
If c* >= 1: identifies bottleneck residue classes for Phase 2.

Single-threaded (LP solver is the bottleneck, not transition computation).
"""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix, csc_matrix
import time, json, os, sys

def syr_d_exact(r, d):
    """Exact d-step accelerated Syracuse on odd integer r."""
    cur = r
    total_S = 0
    for _ in range(d):
        val = 3 * cur + 1
        v = (val & -val).bit_length() - 1
        cur = val >> v
        total_S += v
    return cur, total_S

def solve_lyapunov(k, d):
    """Solve LP for optimal contraction c* with modulus 2^k and d steps."""
    M = 1 << k
    odds = list(range(1, M, 2))
    n = len(odds)
    idx = {r: i for i, r in enumerate(odds)}

    # Compute transitions (fast, single-threaded)
    trans = {}
    for r in odds:
        final, S = syr_d_exact(r, d)
        trans[r] = (final % M, S)

    max_S = max(S for _, S in trans.values())
    min_S = min(S for _, S in trans.values())

    # Build sparse LP matrix
    # minimize t s.t. (d·log2(3) - S(r)) + u[r'] - u[r] <= t
    lg3 = np.log2(3)

    A = lil_matrix((n, n + 1))
    b = np.zeros(n)

    for j, r in enumerate(odds):
        rf, S = trans[r]
        irf = idx[rf]
        A[j, irf] += 1.0
        A[j, j]   -= 1.0
        A[j, n]    = -1.0
        b[j] = S - d * lg3

    c_obj = np.zeros(n + 1)
    c_obj[n] = 1.0

    Aeq = lil_matrix((1, n + 1))
    Aeq[0, 0] = 1.0
    beq = [0.0]

    bounds = [(None, None)] * (n + 1)

    res = linprog(c_obj, A_ub=csc_matrix(A), b_ub=b,
                  A_eq=csc_matrix(Aeq), b_eq=beq,
                  bounds=bounds, method='highs')

    if res.success:
        t_opt = res.x[n]
        c_star = 2.0 ** t_opt
        log_w = res.x[:n]

        # Find worst-case residue classes
        worst = []
        for j, r in enumerate(odds):
            rf, S = trans[r]
            irf = idx[rf]
            slack = t_opt - (d * lg3 - S + log_w[irf] - log_w[j])
            worst.append((slack, r, rf, S, d * lg3 - S))
        worst.sort()

        return {
            'k': k, 'd': d, 'c_star': float(c_star),
            'log2_c': float(t_opt),
            'n_residues': n,
            'max_shift': int(max_S), 'min_shift': int(min_S),
            'weight_range': [float(2**min(log_w)), float(2**max(log_w))],
            'worst_5': [(float(sl), int(r), int(rf), int(S), float(lg))
                        for sl, r, rf, S, lg in worst[:5]],
            'ok': True
        }
    return {'k': k, 'd': d, 'ok': False, 'msg': str(res.message)}


def main():
    t_start = time.time()

    print("=" * 70)
    print("  LYAPUNOV FUNCTION SEARCH FOR COLLATZ CONJECTURE")
    print("  V(n) = n · w[n mod 2^k],  d-step contraction LP")
    print("=" * 70)
    print(flush=True)

    params = [
        (4, 1), (4, 2), (4, 3), (4, 5), (4, 10),
        (6, 1), (6, 2), (6, 3), (6, 5), (6, 10),
        (8, 1), (8, 2), (8, 3), (8, 5), (8, 10),
        (10, 1), (10, 2), (10, 3), (10, 5), (10, 10),
        (12, 1), (12, 2), (12, 3), (12, 5),
        (14, 1), (14, 2), (14, 3),
    ]

    results = []
    print(f"{'k':>4} {'d':>3} | {'c*':>12} | {'log2(c*)':>10} | {'shifts':>10} | {'weights':>24} | {'time':>6}")
    print("-" * 85)

    for k, d in params:
        sys.stdout.flush()
        t0 = time.time()
        r = solve_lyapunov(k, d)
        dt = time.time() - t0
        results.append(r)

        if r['ok']:
            c = r['c_star']
            flag = " 🔥 BREAKTHROUGH!" if c < 1.0 else ""
            wr = r['weight_range']
            print(f"{k:>4} {d:>3} | {c:>12.8f} | {r['log2_c']:>+10.6f} | "
                  f"{r['min_shift']:>3}..{r['max_shift']:<4} | "
                  f"{wr[0]:.2e}..{wr[1]:.2e} | {dt:>5.1f}s{flag}", flush=True)
        else:
            print(f"{k:>4} {d:>3} | {'FAILED':>12} | {r.get('msg','')[:30]:>30} | {dt:>5.1f}s", flush=True)

    print()
    print("=" * 70)
    print("INTERPRETATION:")
    print("  c* < 1  =>  Lyapunov function EXISTS!")
    print("  c* >= 1 =>  periodic weights insufficient at this (k, d)")
    print("=" * 70)

    ok_results = [r for r in results if r.get('ok')]
    if ok_results:
        best = min(ok_results, key=lambda r: r['c_star'])
        print(f"\nBest: k={best['k']}, d={best['d']}, c* = {best['c_star']:.8f}")
        if best['c_star'] < 1.0:
            print("*** LYAPUNOV FUNCTION FOUND! ***")
        else:
            print(f"Gap: c* - 1 = {best['c_star'] - 1:.8f}")
            print("\nBottleneck residues (tightest constraints):")
            for sl, r, rf, S, lg in best['worst_5']:
                print(f"  r={r:>6} -> {rf:>6}  S={S:>3}  "
                      f"log2(3^d/2^S)={lg:>+.4f}  slack={sl:.6f}")

    os.makedirs("data", exist_ok=True)
    with open("data/lyapunov_search.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to data/lyapunov_search.json")
    print(f"Total: {time.time() - t_start:.1f}s")

if __name__ == "__main__":
    main()
