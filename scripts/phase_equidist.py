"""
Test: is the phase theta(j, l_j) at renewal points approximately uniform on [0,1)?
If yes, then P(black) = 2*eps and rho = 1 - 2*eps follows trivially.

We also test:
1. Marginal distribution of theta at renewal points (histogram)
2. Correlation between consecutive renewal phases
3. Comparison with exact uniform prediction
"""
import random
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor

def theta_val(j, l, n, xi):
    """Full phase theta(j,l) in [0,1) using exact modular arithmetic (Tao eq 7.8)."""
    M = 3**n
    inv2 = (M + 1) // 2
    two_inv = pow(inv2, l - 1, M)
    r = (xi * pow(3, 2*j - 2, M) * two_inv) % M
    return r / float(M)

def theta_dist(j, l, n, xi):
    """||theta|| = distance to nearest integer."""
    x = theta_val(j, l, n, xi)
    return min(x, 1.0 - x)

def geom2():
    k = 1
    while random.random() > 0.5:
        k += 1
    return k

def collect_phases(args):
    n, xi, num_paths = args
    max_j = n // 2
    phases = []
    consecutive_pairs = []
    
    for _ in range(num_paths):
        l = 0
        prev_theta = None
        for j in range(1, max_j + 1):
            b = geom2() + geom2()
            l += b
            if b == 3:  # renewal point
                th = theta_val(j, l, n, xi)
                phases.append(th)
                if prev_theta is not None:
                    consecutive_pairs.append((prev_theta, th))
                prev_theta = th
    
    return phases, consecutive_pairs

def ks_test_uniform(samples):
    """Kolmogorov-Smirnov statistic against Uniform[0,1)."""
    s = np.sort(samples)
    n = len(s)
    D = np.max(np.abs(s - np.arange(1, n+1)/n))
    # Critical value at 5%: 1.36/sqrt(n)
    crit = 1.36 / math.sqrt(n)
    return D, crit

def main():
    print("=== Phase Equidistribution Test at Renewal Points ===\n", flush=True)
    
    configs = [
        (10, 1), (10, 5), (10, 7),
        (20, 1), (20, 4), (20, 8),
        (40, 1), (40, 2), (40, 5),
        (60, 1), (60, 7),
        (80, 1), (80, 4),
        (100, 1), (100, 2),
    ]
    num_paths = 20000
    
    print(f"{'n':<5} {'xi':<4} | {'#phases':<8} | {'KS stat':<10} {'KS crit':<10} {'uniform?':<10} | "
          f"{'mean':<8} {'std':<8} | {'corr(k,k+1)':<12}", flush=True)
    print("-" * 95, flush=True)
    
    with ProcessPoolExecutor(max_workers=28) as executor:
        tasks = [(n, xi, num_paths) for n, xi in configs]
        results = list(executor.map(collect_phases, tasks))
    
    for (n, xi), (phases, pairs) in zip(configs, results):
        phases = np.array(phases)
        N = len(phases)
        
        if N < 10:
            print(f"{n:<5} {xi:<4} | {N:<8} | insufficient data")
            continue
        
        # KS test
        D, crit = ks_test_uniform(phases)
        is_uniform = "YES" if D < crit else "NO"
        
        # Mean and std (uniform: mean=0.5, std=1/sqrt(12)≈0.2887)
        m = np.mean(phases)
        s = np.std(phases)
        
        # Correlation between consecutive renewal phases
        if len(pairs) > 10:
            p1 = np.array([p[0] for p in pairs])
            p2 = np.array([p[1] for p in pairs])
            corr = np.corrcoef(p1, p2)[0, 1]
        else:
            corr = float('nan')
        
        print(f"{n:<5} {xi:<4} | {N:<8} | {D:<10.4f} {crit:<10.4f} {is_uniform:<10} | "
              f"{m:<8.4f} {s:<8.4f} | {corr:<12.4f}", flush=True)
    
    # Detailed histogram for one case
    print("\n=== Histogram: n=40, xi=1 (20 bins) ===", flush=True)
    phases_40, _ = collect_phases((40, 1, 50000))
    phases_40 = np.array(phases_40)
    counts, edges = np.histogram(phases_40, bins=20, range=(0, 1))
    expected = len(phases_40) / 20
    print(f"Expected per bin (uniform): {expected:.1f}", flush=True)
    for i in range(20):
        bar = "#" * int(counts[i] / expected * 30)
        print(f"  [{edges[i]:.2f}, {edges[i+1]:.2f}): {counts[i]:6d}  {bar}", flush=True)
    
    chi2 = np.sum((counts - expected)**2 / expected)
    print(f"\nChi-squared statistic: {chi2:.2f} (critical at 5%, 19 df: 30.14)", flush=True)
    print(f"Uniform? {'YES' if chi2 < 30.14 else 'NO'}", flush=True)

if __name__ == '__main__':
    main()
