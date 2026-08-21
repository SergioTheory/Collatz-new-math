"""
Attack D v2: Refined multi-block survival with Qwen's protocol.

1. B = 20, 24, 28, 32 at alpha = 1.10 (and 1.05 for robustness)
2. Three-parameter fit: S(k) = c^k * k^{-gamma}
3. Extrapolation c(B) vs 1/B
4. MAX_STEPS = 1000 to see ratio plateau
"""

import numpy as np
from numba import njit
from multiprocessing.dummy import Pool as ThreadPool
import math
import time
from scipy.optimize import curve_fit


@njit(nogil=True)
def compute_passage_times(starts, n0, max_steps):
    n = len(starts)
    times = np.full(n, max_steps, dtype=np.int32)
    overflow_limit = np.int64(1) << np.int64(62)
    for i in range(n):
        x = starts[i]
        for step in range(1, max_steps + 1):
            x = np.int64(3) * x + np.int64(1)
            while x & np.int64(1) == np.int64(0):
                x >>= np.int64(1)
            if x < n0:
                times[i] = np.int32(step)
                break
            if x > overflow_limit:
                break
    return times


def run_experiment(B, alpha, max_steps=1000, num_workers=20):
    n0 = np.int64(1) << np.int64(B)
    upper = int(float(n0) ** alpha)
    lo = int(n0) | 1
    total = (upper - lo) // 2
    if upper % 2 != 0:
        total += 1

    if total > 10**7:
        rng = np.random.default_rng(42 + B)
        # Generate random indices directly to avoid MemoryError.
        # Using integers (with replacement) is perfectly fine since 10^7 << total (which is ~10^10).
        # Collisions will be virtually zero.
        idx = rng.integers(0, total, size=10**7)
        starts = lo + 2 * idx
        total_for_stats = total
        sampled = True
    else:
        starts = np.arange(lo, upper, 2, dtype=np.int64)
        total_for_stats = total
        sampled = False

    chunks = np.array_split(starts, num_workers)
    with ThreadPool(num_workers) as pool:
        results = pool.starmap(
            compute_passage_times,
            [(c, n0, max_steps) for c in chunks]
        )
    all_times = np.concatenate(results)
    return all_times, len(starts), sampled


def three_param_fit(ks, log_s):
    """Fit log S(k) = k*log(c) - gamma*log(k) + const."""
    def model(k, log_c, gamma, const):
        return k * log_c - gamma * np.log(k) + const

    try:
        popt, pcov = curve_fit(model, ks, log_s, p0=[-0.7, 1.0, 0.0], maxfev=5000)
        log_c, gamma, const = popt
        c_star = math.exp(log_c)
        fitted = model(ks, *popt)
        ss_res = np.sum((log_s - fitted)**2)
        ss_tot = np.sum((log_s - np.mean(log_s))**2)
        r2 = 1 - ss_res / ss_tot
        return c_star, gamma, r2
    except Exception:
        return None, None, None


def analyze(times, total, B, alpha, block_size=10):
    max_t = int(times.max())
    max_blocks = min(max_t // block_size, 30)

    survival_data = []
    for k in range(0, max_blocks + 1):
        T = k * block_size
        count = int(np.sum(times > T))
        s = count / total
        survival_data.append((k, T, s, count))
        if count < 10:
            break

    # Print survival curve
    print(f"\n  Survival curve (d={block_size}):")
    print(f"  {'k':>4} | {'T':>5} | {'S(T)':>12} | {'ratio':>8} | {'#surv':>8}")
    print(f"  " + "-" * 50)
    prev_s = 1.0
    for k, T, s, cnt in survival_data:
        ratio = s / prev_s if prev_s > 0 and k > 0 else 1.0
        if k <= 20 or k % 5 == 0:
            print(f"  {k:>4} | {T:>5} | {s:>12.6f} | {ratio:>8.4f} | {cnt:>8}")
        prev_s = s

    # Three-parameter fit: S(k) = c^k * k^{-gamma}
    valid = [(k, s) for k, _, s, cnt in survival_data if k >= 1 and cnt >= 50]
    if len(valid) < 4:
        print("  Too few valid points for fit")
        return None, None

    ks = np.array([v[0] for v in valid], dtype=np.float64)
    log_s = np.array([np.log(v[1]) for v in valid], dtype=np.float64)

    c_star, gamma, r2 = three_param_fit(ks, log_s)

    # Also pure geometric for comparison
    coeffs_geo = np.polyfit(ks, log_s, 1)
    c_geo = math.exp(coeffs_geo[0])
    fitted_geo = np.polyval(coeffs_geo, ks)
    r2_geo = 1 - np.sum((log_s - fitted_geo)**2) / np.sum((log_s - np.mean(log_s))**2)

    print(f"\n  Fits (blocks {int(ks[0])}..{int(ks[-1])}, {len(valid)} pts):")
    print(f"    Pure geometric:       S(k) ~ {c_geo:.4f}^k             R2 = {r2_geo:.6f}")
    if c_star is not None:
        print(f"    Three-param (Qwen):   S(k) ~ {c_star:.4f}^k * k^(-{gamma:.2f})  R2 = {r2:.6f}")
        print(f"    => c* = {c_star:.4f}, gamma = {gamma:.2f}")
    else:
        print(f"    Three-param fit failed")
        c_star = c_geo
        gamma = 0.0

    return c_star, gamma


if __name__ == "__main__":
    configs = [
        (20, 1.05),
        (20, 1.10),
        (24, 1.05),
        (24, 1.10),
        (28, 1.05),
        (28, 1.10),
        (32, 1.05),
        (32, 1.10),
    ]

    MAX_STEPS = 1000
    BLOCK = 10

    print("=" * 70)
    print("ATTACK D v2: c(B) trend diagnostic")
    print(f"MAX_STEPS={MAX_STEPS}, block={BLOCK}")
    print("Fit: S(k) = c*^k * k^(-gamma) [Qwen protocol]")
    print("=" * 70)

    results_by_alpha = {}

    for B, alpha in configs:
        key = alpha
        if key not in results_by_alpha:
            results_by_alpha[key] = []

        print(f"\n{'='*70}")
        print(f"B = {B}, alpha = {alpha}, interval [2^{B}, 2^{B*alpha:.1f}]")

        t0 = time.time()
        times, total, sampled = run_experiment(B, alpha, MAX_STEPS, num_workers=20)
        t1 = time.time()

        tag = "sampled" if sampled else "exhaustive"
        print(f"  {total:,} trajectories ({tag}) in {t1-t0:.1f}s")
        survived = int(np.sum(times >= MAX_STEPS))
        print(f"  Survivors (T>={MAX_STEPS}): {survived} ({survived/total*100:.4f}%)")

        c_star, gamma = analyze(times, total, B, alpha, BLOCK)
        if c_star is not None:
            results_by_alpha[key].append((B, c_star, gamma))

    # Extrapolation: c(B) vs 1/B
    print(f"\n{'='*70}")
    print("EXTRAPOLATION: c*(B) vs 1/B")
    print("=" * 70)

    for alpha, data in sorted(results_by_alpha.items()):
        if len(data) < 3:
            continue

        print(f"\nalpha = {alpha}:")
        Bs = np.array([d[0] for d in data], dtype=np.float64)
        cs = np.array([d[1] for d in data], dtype=np.float64)
        gammas = np.array([d[2] for d in data], dtype=np.float64)

        print(f"  {'B':>4} | {'c*':>8} | {'gamma':>8} | {'1/B':>8} | {'increment':>10}")
        print(f"  " + "-" * 48)
        for i, (b, c, g) in enumerate(data):
            inc = f"{c - data[i-1][1]:+.4f}" if i > 0 else "   ---"
            print(f"  {int(b):>4} | {c:>8.4f} | {g:>8.2f} | {1/b:>8.4f} | {inc:>10}")

        # Fit c(B) = c_inf + A/B (saturation model)
        inv_B = 1.0 / Bs
        try:
            coeffs_sat = np.polyfit(inv_B, cs, 1)
            c_inf_sat = coeffs_sat[1]  # intercept = c at B->inf
            print(f"\n  Linear fit c(B) = {c_inf_sat:.4f} + {coeffs_sat[0]:.2f}/B")
            print(f"  => c(B->inf) = {c_inf_sat:.4f}")
        except:
            c_inf_sat = None

        # Fit c(B) = c_inf + A/log(B) (log saturation)
        inv_logB = 1.0 / np.log(Bs)
        try:
            coeffs_log = np.polyfit(inv_logB, cs, 1)
            c_inf_log = coeffs_log[1]
            print(f"  Log fit c(B) = {c_inf_log:.4f} + {coeffs_log[0]:.2f}/ln(B)")
            print(f"  => c(B->inf) = {c_inf_log:.4f}")
        except:
            c_inf_log = None

        # Verdict
        increments = [data[i][1] - data[i-1][1] for i in range(1, len(data))]
        print(f"\n  Increments: {['%.4f' % x for x in increments]}")
        if len(increments) >= 3:
            if increments[-1] < increments[0] * 0.5:
                print(f"  => INCREMENT SHRINKING: supports c* < 1, dim_H < 1")
            elif increments[-1] > increments[0] * 0.8:
                print(f"  => INCREMENT STABLE: suggests c -> 1, dim_H = 1")
            else:
                print(f"  => AMBIGUOUS: need more B values")

        if c_inf_sat is not None:
            if c_inf_sat < 0.95:
                print(f"  => EXTRAPOLATION c(inf) = {c_inf_sat:.4f} < 1: supports dim_H < 1")
            else:
                print(f"  => EXTRAPOLATION c(inf) = {c_inf_sat:.4f} ~ 1: suggests dim_H = 1")

    print(f"\n{'='*70}")
    print("END OF ATTACK D v2")
