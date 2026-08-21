"""
Attack D: Multi-block survival diagnostic.

GOAL: Measure c(N_0) = per-block survival coefficient.
  - Geometric decay S(k) ~ c^k  =>  dim_H < 1 (conditional on transport)
  - Power-law tail   S(k) ~ k^{-beta}  =>  dim_H = 1 (attack falsified)

Both outcomes are valuable. This is a NUMERICAL OBSERVATION,
not a route to pointwise closure.

Method:
  For each odd N in [N_0, N_0^alpha]:
    Run accelerated Syracuse map x -> (3x+1) / 2^{v_2(3x+1)}
    Record first-passage time T = min{k >= 1 : x_k < N_0}
  Compute survival curve S(T) and per-block survival ratios.

Parameters: N_0 = 2^B, B in {20, 24}, alpha in {1.05, 1.10, 1.20}
"""

import numpy as np
from numba import njit
from multiprocessing.dummy import Pool as ThreadPool
import math
import time


@njit(nogil=True)
def compute_passage_times(starts, n0, max_steps):
    """Compute first-passage time below n0 for each start."""
    n = len(starts)
    times = np.full(n, max_steps, dtype=np.int32)
    overflow_limit = np.int64(1) << np.int64(62)

    for i in range(n):
        x = starts[i]
        for step in range(1, max_steps + 1):
            # Accelerated Syracuse step: x -> (3x+1) / 2^v
            x = np.int64(3) * x + np.int64(1)
            while x & np.int64(1) == np.int64(0):
                x >>= np.int64(1)
            if x < n0:
                times[i] = np.int32(step)
                break
            if x > overflow_limit:
                # Orbit escaped to huge values -- treat as survivor
                break
    return times


def run_experiment(B, alpha, max_steps=500, num_workers=20):
    """Run the survival experiment for given barrier and exponent."""
    n0 = np.int64(1) << np.int64(B)
    upper = int(float(n0) ** alpha)

    # Collect odd numbers in [n0, upper)
    lo = int(n0) | 1
    starts = np.arange(lo, upper, 2, dtype=np.int64)
    total = len(starts)

    if total > 10**7:
        # Sample 10^7 for large ranges
        rng = np.random.default_rng(42)
        idx = rng.choice(total, size=10**7, replace=False)
        starts = starts[idx]
        total = len(starts)
        sampled = True
    else:
        sampled = False

    # Split into chunks for parallel processing
    chunks = np.array_split(starts, num_workers)

    with ThreadPool(num_workers) as pool:
        results = pool.starmap(
            compute_passage_times,
            [(c, n0, max_steps) for c in chunks]
        )

    all_times = np.concatenate(results)
    return all_times, total, sampled


def analyze_survival(times, total, B, alpha, block_size=10):
    """Analyze the survival curve and per-block ratios."""
    max_t = times.max()
    max_blocks = min(max_t // block_size, 20)

    print(f"\n  Survival curve (block = {block_size} Syracuse steps):")
    print(f"  {'block k':>8} | {'T = k*d':>8} | {'S(T)':>12} | {'S(k)/S(k-1)':>12} | {'survivors':>10}")
    print(f"  " + "-" * 60)

    survival = []
    prev_s = 1.0
    for k in range(0, max_blocks + 1):
        T = k * block_size
        count = np.sum(times > T)
        s = count / total
        ratio = s / prev_s if prev_s > 0 and k > 0 else 1.0
        survival.append((k, T, s, ratio, count))
        if k <= 15 or k % 5 == 0:
            print(f"  {k:>8} | {T:>8} | {s:>12.6f} | {ratio:>12.4f} | {count:>10}")
        prev_s = s
        if count < 10:
            break

    # Diagnostic: fit log(S) vs k for blocks with enough survivors (>100)
    valid = [(k, s) for k, _, s, _, cnt in survival if k >= 1 and cnt >= 100]

    if len(valid) >= 3:
        ks = np.array([v[0] for v in valid], dtype=np.float64)
        log_s = np.array([np.log(v[1]) for v in valid], dtype=np.float64)

        # Linear fit: log(S) = a + b*k  =>  S ~ e^{bk} = c^k, c = e^b
        coeffs = np.polyfit(ks, log_s, 1)
        b_geo = coeffs[0]
        c_geo = math.exp(b_geo)
        r2_geo = 1 - np.sum((log_s - np.polyval(coeffs, ks))**2) / np.sum((log_s - np.mean(log_s))**2)

        # Power-law fit: log(S) = a - beta*log(k)
        log_ks = np.log(ks)
        coeffs_pl = np.polyfit(log_ks, log_s, 1)
        beta_pl = -coeffs_pl[0]
        r2_pl = 1 - np.sum((log_s - np.polyval(coeffs_pl, log_ks))**2) / np.sum((log_s - np.mean(log_s))**2)

        print(f"\n  Fit diagnostics (blocks {int(ks[0])}..{int(ks[-1])}, {len(valid)} points):")
        print(f"    Geometric fit: S(k) ~ {c_geo:.4f}^k  (R^2 = {r2_geo:.4f})")
        print(f"    Power-law fit: S(k) ~ k^(-{beta_pl:.2f})  (R^2 = {r2_pl:.4f})")

        if r2_geo > r2_pl + 0.02:
            print(f"    => GEOMETRIC wins: per-block survival c = {c_geo:.4f}")
            print(f"    => Supports dim_H < 1 (conditional on transport)")
        elif r2_pl > r2_geo + 0.02:
            print(f"    => POWER-LAW wins: tail exponent beta = {beta_pl:.2f}")
            print(f"    => Supports dim_H = 1 (attack D falsified)")
        else:
            print(f"    => INCONCLUSIVE: fits too close (delta R^2 = {abs(r2_geo-r2_pl):.4f})")

        # Also check if per-block ratio is increasing (power-law sign)
        ratios = [r for _, _, _, r, cnt in survival if cnt >= 100]
        if len(ratios) >= 5:
            early = np.mean(ratios[1:4])
            late = np.mean(ratios[-3:])
            print(f"    Per-block ratio: early = {early:.4f}, late = {late:.4f}", end="")
            if late > early + 0.02:
                print(" (INCREASING => power-law tail)")
            elif abs(late - early) < 0.02:
                print(" (STABLE => geometric)")
            else:
                print(f" (DECREASING => super-geometric)")
    else:
        print(f"\n  Too few valid blocks ({len(valid)}) for fit diagnostic")

    return survival


if __name__ == "__main__":
    configs = [
        (20, 1.05),
        (20, 1.10),
        (20, 1.20),
        (24, 1.10),
    ]

    MAX_STEPS = 500
    BLOCK_SIZE = 10  # Syracuse steps per block

    print("=" * 70)
    print("ATTACK D: Multi-block survival diagnostic")
    print(f"Max steps: {MAX_STEPS}, Block size: {BLOCK_SIZE}")
    print("Geometric S(k)~c^k => dim_H < 1 | Power-law S(k)~k^(-b) => dim_H = 1")
    print("=" * 70)

    for B, alpha in configs:
        print(f"\n{'='*70}")
        print(f"N_0 = 2^{B}, alpha = {alpha}")
        print(f"Interval: [2^{B}, 2^{B*alpha:.1f}]")

        t0 = time.time()
        times, total, sampled = run_experiment(B, alpha, MAX_STEPS, num_workers=20)
        t1 = time.time()

        tag = f" (sampled {total:,})" if sampled else f" (exhaustive {total:,})"
        print(f"Computed {total:,} trajectories{tag} in {t1-t0:.1f}s")

        # Basic stats
        median_t = np.median(times)
        mean_t = np.mean(times)
        survived = np.sum(times >= MAX_STEPS)
        print(f"Median first-passage: {median_t:.0f} steps")
        print(f"Mean first-passage:   {mean_t:.1f} steps")
        print(f"Survivors (T >= {MAX_STEPS}): {survived} ({survived/total*100:.4f}%)")

        analyze_survival(times, total, B, alpha, BLOCK_SIZE)

    print(f"\n{'='*70}")
    print("END OF DIAGNOSTIC")
