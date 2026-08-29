"""
lyapunov_ml_search.py — Phase 2: ML-guided Lyapunov function search.

Three approaches:
A. Feature-based LP: V(n) = n · exp(Σ c_i · f_i(n))
   Features: bit density, low-bit residues, trailing patterns
B. Modular weights on REAL large numbers: V(n) = n · w[n mod M]
   (fixes Phase 1 bug: uses actual large n, not small representatives)
C. Worst-case analysis: find the "hardest" numbers (highest Syr^d(n)/n)

Uses numba + prange for 30-core parallel Syr^d computation.
Estimated runtime: ~2-3 minutes (including numba JIT compilation).
"""
import numpy as np
from numba import njit, prange
from scipy.optimize import linprog
from scipy.sparse import csc_matrix
import time, json, os, sys

OVERFLOW = 10**17

# ──────────────────────────────────────────────
# 1. NUMBA KERNELS (parallelized across 30 cores)
# ──────────────────────────────────────────────

@njit
def syr_d(n, d):
    """d-step accelerated Syracuse. Returns -1 on overflow."""
    cur = n
    for _ in range(d):
        cur = 3 * cur + 1
        while cur % 2 == 0:
            cur //= 2
        if cur > OVERFLOW:
            return -1
    return cur

@njit(parallel=True)
def batch_syr(starts, d):
    """Parallel Syr^d for an array of odd starting values."""
    n = len(starts)
    finals = np.empty(n, dtype=np.int64)
    ratios = np.empty(n, dtype=np.float64)
    for i in prange(n):
        s = syr_d(starts[i], d)
        finals[i] = s
        ratios[i] = s / starts[i] if s > 0 else -1.0
    return finals, ratios

@njit
def popcount64(x):
    c = 0
    while x > 0:
        c += x & 1
        x >>= 1
    return c

@njit
def bitlen64(x):
    c = 0
    while x > 0:
        c += 1
        x >>= 1
    return c

@njit
def trailing_ones(x):
    c = 0
    while x & 1:
        c += 1
        x >>= 1
    return c

@njit
def v2(x):
    c = 0
    while x > 0 and x % 2 == 0:
        c += 1
        x //= 2
    return c

@njit(parallel=True)
def compute_features(arr):
    """Compute 10 structural features for each number."""
    n = len(arr)
    feats = np.empty((n, 10), dtype=np.float64)
    for i in prange(n):
        x = arr[i]
        if x <= 0:
            for j in range(10):
                feats[i, j] = 0.0
            continue
        bl = bitlen64(x)
        pc = popcount64(x)
        feats[i, 0] = pc / bl          # bit density
        feats[i, 1] = (x % 4) / 4.0    # residue mod 4
        feats[i, 2] = (x % 8) / 8.0    # mod 8
        feats[i, 3] = (x % 16) / 16.0  # mod 16
        feats[i, 4] = (x % 32) / 32.0  # mod 32
        feats[i, 5] = (x % 64) / 64.0  # mod 64
        feats[i, 6] = (x % 128) / 128.0
        feats[i, 7] = (x % 256) / 256.0
        feats[i, 8] = trailing_ones(x) / bl  # trailing 1s ratio
        feats[i, 9] = v2(x + 1) / bl        # v2(n+1) ratio
    return feats


# ──────────────────────────────────────────────
# 2. SAMPLE GENERATION
# ──────────────────────────────────────────────

def generate_odd_samples(N, lo=10**6, hi=10**9):
    """Generate N random odd numbers in [lo, hi]."""
    rng = np.random.default_rng(42)
    arr = rng.integers(lo // 2, hi // 2, size=N, dtype=np.int64)
    return 2 * arr + 1  # guaranteed odd


# ──────────────────────────────────────────────
# 3. APPROACH A: Feature-based LP
# ──────────────────────────────────────────────

def approach_a(starts, finals, ratios, d):
    """Feature-based LP: V(n) = n · exp(Σ c_i · f_i(n))."""
    print(f"\n{'='*60}")
    print(f"  APPROACH A: Feature-based LP (d={d})")
    print(f"{'='*60}")

    # Filter out overflows
    mask = finals > 0
    starts_ok = starts[mask]
    finals_ok = finals[mask]
    ratios_ok = ratios[mask]
    N = len(starts_ok)
    print(f"  Samples: {N} (removed {(~mask).sum()} overflows)")

    # Compute features
    t0 = time.time()
    feats_start = compute_features(starts_ok)
    feats_final = compute_features(finals_ok)
    delta_feats = feats_final - feats_start
    log_ratios = np.log2(ratios_ok)
    print(f"  Features computed in {time.time()-t0:.1f}s")

    # Stats
    print(f"  Ratio stats: min={ratios_ok.min():.6f}, "
          f"median={np.median(ratios_ok):.6f}, "
          f"max={ratios_ok.max():.6f}")
    print(f"  log2(ratio) max = {log_ratios.max():.4f} "
          f"({'GROWTH' if log_ratios.max() > 0 else 'decay'})")

    # LP: minimize t s.t. log_ratio[i] + Σ c_j · Δf_j[i] ≤ t
    # Variables: c_0..c_9, t  (11 total)
    p = delta_feats.shape[1]
    A_ub = np.hstack([delta_feats, -np.ones((N, 1))])
    b_ub = -log_ratios

    c_obj = np.zeros(p + 1)
    c_obj[p] = 1.0

    bounds = [(-50, 50)] * p + [(None, None)]

    t0 = time.time()
    res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    dt = time.time() - t0

    if res.success:
        t_opt = res.x[p]
        c_star = 2.0 ** t_opt
        coeffs = res.x[:p]

        feat_names = ['bit_dens', 'mod4', 'mod8', 'mod16', 'mod32',
                       'mod64', 'mod128', 'mod256', 'trail1s', 'v2(n+1)']
        print(f"\n  LP solved in {dt:.1f}s")
        print(f"  Optimal t = {t_opt:.6f}, c* = 2^t = {c_star:.8f}")

        if c_star < 1.0:
            print(f"  🔥🔥🔥 c* < 1!!! LYAPUNOV CANDIDATE FOUND! 🔥🔥🔥")
        else:
            print(f"  c* >= 1 (gap = {c_star - 1:.6f})")

        print(f"\n  Learned coefficients:")
        for i, (name, c) in enumerate(zip(feat_names, coeffs)):
            if abs(c) > 0.01:
                print(f"    {name:>10}: {c:+.4f}")

        return {'c_star': float(c_star), 'log2_c': float(t_opt),
                'coeffs': {n: float(c) for n, c in zip(feat_names, coeffs)},
                'ok': True}
    else:
        print(f"  LP FAILED: {res.message}")
        return {'ok': False}


# ──────────────────────────────────────────────
# 4. APPROACH B: Modular weights on real data
# ──────────────────────────────────────────────

def approach_b(starts, finals, ratios, d, M=256):
    """Modular weights LP on real large numbers."""
    print(f"\n{'='*60}")
    print(f"  APPROACH B: Modular weights mod {M} on real data (d={d})")
    print(f"{'='*60}")

    mask = finals > 0
    starts_ok = starts[mask]
    finals_ok = finals[mask]
    ratios_ok = ratios[mask]
    N = len(starts_ok)

    n_classes = M // 2  # odd classes
    idx = {}
    for i, r in enumerate(range(1, M, 2)):
        idx[r] = i

    log_ratios = np.log2(ratios_ok)

    # LP: minimize t s.t. log_ratio[i] + u[final mod M] - u[start mod M] ≤ t
    # Variables: u_0..u_{n_classes-1}, t
    from scipy.sparse import lil_matrix as lil

    A = lil((N, n_classes + 1))
    b = np.zeros(N)

    for i in range(N):
        r_start = int(starts_ok[i] % M)
        r_final = int(finals_ok[i] % M)
        # Make sure they're odd (they should be)
        if r_start % 2 == 0:
            r_start = (r_start + 1) % M
        if r_final % 2 == 0:
            r_final = (r_final + 1) % M

        j_start = idx.get(r_start)
        j_final = idx.get(r_final)
        if j_start is None or j_final is None:
            continue

        A[i, j_final] += 1.0
        A[i, j_start] -= 1.0
        A[i, n_classes] = -1.0
        b[i] = -log_ratios[i]

    c_obj = np.zeros(n_classes + 1)
    c_obj[n_classes] = 1.0

    # Normalize: u[0] = 0
    Aeq = lil((1, n_classes + 1))
    Aeq[0, 0] = 1.0
    beq = [0.0]

    bounds = [(None, None)] * (n_classes + 1)

    t0 = time.time()
    res = linprog(c_obj, A_ub=csc_matrix(A), b_ub=b,
                  A_eq=csc_matrix(Aeq), b_eq=beq,
                  bounds=bounds, method='highs')
    dt = time.time() - t0

    if res.success:
        t_opt = res.x[n_classes]
        c_star = 2.0 ** t_opt

        log_w = res.x[:n_classes]
        print(f"  LP solved in {dt:.1f}s")
        print(f"  c* = {c_star:.8f} (log2 = {t_opt:+.6f})")
        print(f"  Weight range: {2**min(log_w):.2e} .. {2**max(log_w):.2e}")

        if c_star < 1.0:
            print(f"  🔥 c* < 1 with mod-{M} weights on REAL data!")
        else:
            print(f"  c* >= 1 (gap = {c_star - 1:.6f})")

        return {'M': M, 'c_star': float(c_star), 'log2_c': float(t_opt), 'ok': True}
    else:
        print(f"  FAILED: {res.message}")
        return {'ok': False}


# ──────────────────────────────────────────────
# 5. APPROACH C: Worst-case analysis
# ──────────────────────────────────────────────

def approach_c(starts, finals, ratios, d):
    """Find and analyze the hardest numbers."""
    print(f"\n{'='*60}")
    print(f"  APPROACH C: Worst-case analysis (d={d})")
    print(f"{'='*60}")

    mask = finals > 0
    ratios_ok = ratios[mask]
    starts_ok = starts[mask]
    finals_ok = finals[mask]

    # Top 20 worst cases
    top_idx = np.argsort(ratios_ok)[-20:][::-1]
    print(f"\n  Top 20 worst cases (highest Syr^{d}(n)/n):")
    print(f"  {'n':>15} {'Syr^d(n)':>15} {'ratio':>10} {'bits':>5} "
          f"{'popcount':>8} {'n%8':>4} {'n%16':>5} {'trail1s':>7}")
    print("  " + "-" * 85)

    for i in top_idx:
        n = int(starts_ok[i])
        s = int(finals_ok[i])
        r = ratios_ok[i]
        bl = int(np.log2(n)) + 1
        pc = bin(n).count('1')
        to = 0
        x = n
        while x & 1:
            to += 1
            x >>= 1
        print(f"  {n:>15} {s:>15} {r:>10.4f} {bl:>5} "
              f"{pc:>8} {n%8:>4} {n%16:>5} {to:>7}")

    # Statistics for growth cases
    growth_mask = ratios_ok > 1.0
    n_growth = growth_mask.sum()
    frac_growth = n_growth / len(ratios_ok)
    print(f"\n  Numbers with Syr^{d}(n) > n: {n_growth}/{len(ratios_ok)} ({frac_growth:.4%})")

    if n_growth > 0:
        growth_ratios = ratios_ok[growth_mask]
        print(f"  Growth ratio: mean={growth_ratios.mean():.4f}, "
              f"max={growth_ratios.max():.4f}")

    return {
        'n_growth': int(n_growth),
        'frac_growth': float(frac_growth),
        'max_ratio': float(ratios_ok.max()),
        'max_ratio_n': int(starts_ok[np.argmax(ratios_ok)])
    }


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    t_total = time.time()

    print("=" * 60)
    print("  PHASE 2: ML-GUIDED LYAPUNOV SEARCH")
    print("  30-core E5-2696v3, numba parallel")
    print("=" * 60)

    N = 500_000
    d_values = [10, 20, 50]

    print(f"\nGenerating {N:,} random odd numbers in [10^6, 10^9]...")
    starts = generate_odd_samples(N, lo=10**6, hi=10**9)
    print(f"Sample ready. Range: [{starts.min()}, {starts.max()}]")

    # Warm up numba JIT
    print("Warming up numba JIT...", end=" ", flush=True)
    t0 = time.time()
    _ = batch_syr(starts[:100], 5)
    _ = compute_features(starts[:100])
    print(f"done ({time.time()-t0:.1f}s)")

    all_results = {}

    for d in d_values:
        print(f"\n\n{'#'*60}")
        print(f"#  d = {d} steps")
        print(f"{'#'*60}")

        print(f"Computing Syr^{d} for {N:,} numbers...", end=" ", flush=True)
        t0 = time.time()
        finals, ratios = batch_syr(starts, d)
        dt = time.time() - t0
        n_ok = (finals > 0).sum()
        print(f"done ({dt:.1f}s, {n_ok:,} valid, {N-n_ok} overflows)")

        res_a = approach_a(starts, finals, ratios, d)
        res_b = approach_b(starts, finals, ratios, d, M=256)
        res_c = approach_c(starts, finals, ratios, d)

        all_results[f"d={d}"] = {
            'approach_a': res_a,
            'approach_b': res_b,
            'approach_c': res_c
        }

    # Summary
    print(f"\n\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"{'d':>5} | {'A: features':>16} | {'B: mod-256':>16} | {'growth%':>10} | {'max ratio':>10}")
    print("-" * 70)
    for d in d_values:
        r = all_results[f"d={d}"]
        ca = r['approach_a'].get('c_star', float('nan'))
        cb = r['approach_b'].get('c_star', float('nan'))
        gr = r['approach_c']['frac_growth']
        mr = r['approach_c']['max_ratio']
        flag_a = "✅" if ca < 1 else "❌"
        flag_b = "✅" if cb < 1 else "❌"
        print(f"{d:>5} | {ca:>12.6f} {flag_a} | {cb:>12.6f} {flag_b} | {gr:>9.4%} | {mr:>10.4f}")

    os.makedirs("data", exist_ok=True)
    with open("data/lyapunov_ml_search.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to data/lyapunov_ml_search.json")
    print(f"Total runtime: {time.time() - t_total:.1f}s")

if __name__ == "__main__":
    main()
