"""
Attack A: Diagnostic of c_inf for the worst-case 3-adic Fourier rate.

Goal: Determine whether c_inf > 0 (exponential decay) or c_inf = 0 (subexponential).
NOT to "close c_inf > 0" -- both outcomes are valuable.

Method: Exact arithmetic (Python ints, no overflow) Monte Carlo.
For each n, we sample 10^7 compositions of s=2n into n parts (each >= 1),
compute Y_n = ? 3^{n-i} ? 2^{-a_{[i,n]}} mod 3^n via the recurrence
y_{k+1} = (3?y_k + 1) ? inv2^{a_k} mod 3^n,
and evaluate Fourier at the worst-case family xi = 2^k mod 3^n.

The key diagnostic: plot -log(max|E[chi]|) / n vs n.
If it stabilizes at c > 0 -> exponential decay.
If it drifts toward 0 -> subexponential (Fourier barrier impassable).

Uses 20 threads with nogil Numba for n <= 20, pure Python for n > 20.
"""

import numpy as np
import math
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial


def sample_composition(n, s, rng):
    """Sample a uniform random composition of s into n parts, each >= 1."""
    # Stars-and-bars: choose n-1 cut points from {1,...,s-1}
    cuts = sorted(rng.sample(range(1, s), n - 1))
    parts = []
    prev = 0
    for c in cuts:
        parts.append(c - prev)
        prev = c
    parts.append(s - prev)
    return parts


def compute_fourier_worker(args):
    """Worker for one batch of MC samples. Pure Python, arbitrary precision."""
    n, s, num_samples, xis, mod3n, seed = args
    rng = random.Random(seed)
    
    # Precompute inv2 table
    inv2 = pow(2, -1, mod3n)
    inv2_table = [pow(inv2, a, mod3n) for a in range(s + 1)]
    
    num_xis = len(xis)
    sum_cos = [0.0] * num_xis
    sum_sin = [0.0] * num_xis
    
    two_pi = 2.0 * math.pi
    mod3n_float = float(mod3n)
    
    for _ in range(num_samples):
        parts = sample_composition(n, s, rng)
        
        # Compute y_n via recurrence
        y = 0
        for i in range(n):
            a = parts[i]
            y = (3 * y + 1) * inv2_table[a] % mod3n
        
        # Evaluate Fourier at each xi
        y_float = float(y)
        for j in range(num_xis):
            angle = -two_pi * float(xis[j]) * y_float / mod3n_float
            sum_cos[j] += math.cos(angle)
            sum_sin[j] += math.sin(angle)
    
    return sum_cos, sum_sin


def run_diagnostic(n, s, total_samples=10**7, num_workers=20):
    """Run MC diagnostic for a single (n, s) pair."""
    mod3n = 3 ** n
    
    # Build worst-case frequency panel: xi = 2^k mod 3^n
    # Focus on k/n in [1.3, 1.7] (near log_23 ~ 1.585)
    xis = set()
    for k in range(max(1, int(1.2 * n)), min(int(1.8 * n) + 1, 3 * n)):
        xi = pow(2, k, mod3n)
        if xi % 3 != 0:
            xis.add(xi)
    # Also add a few random units for comparison
    rng = random.Random(42 + n)
    while len(xis) < 30:
        xi = rng.randint(1, mod3n - 1)
        if xi % 3 != 0:
            xis.add(xi)
    
    xis_list = list(xis)
    
    samples_per_worker = total_samples // num_workers
    args_list = []
    for i in range(num_workers):
        seed = random.randint(0, 2**31 - 1)
        args_list.append((n, s, samples_per_worker, xis_list, mod3n, seed))
    
    with ProcessPoolExecutor(max_workers=num_workers) as pool:
        results = list(pool.map(compute_fourier_worker, args_list))
    
    num_xis = len(xis_list)
    total_cos = [0.0] * num_xis
    total_sin = [0.0] * num_xis
    
    for sc, ss in results:
        for j in range(num_xis):
            total_cos[j] += sc[j]
            total_sin[j] += ss[j]
    
    actual_total = samples_per_worker * num_workers
    magnitudes = []
    for j in range(num_xis):
        mc = total_cos[j] / actual_total
        ms = total_sin[j] / actual_total
        magnitudes.append(math.sqrt(mc**2 + ms**2))
    
    max_mag = max(magnitudes)
    max_idx = magnitudes.index(max_mag)
    max_xi = xis_list[max_idx]
    
    # Check if max_xi is from the 2^k family
    is_2k = max_xi in [pow(2, k, mod3n) for k in range(max(1, int(1.2*n)), min(int(1.8*n)+1, 3*n))]
    
    # Noise floor for this sample size
    noise_floor = 2.0 / math.sqrt(actual_total)
    
    return max_mag, max_xi, is_2k, noise_floor


if __name__ == "__main__":
    # Diagnostic parameters
    # For n <= 20: 10^7 samples (fast, Python ints still manageable)
    # For n > 20: 10^7 samples (slower per sample due to big ints)
    
    test_points = [
        (12, 24),
        (16, 32),
        (20, 40),
        (24, 48),
        (28, 56),
        (32, 64),
    ]
    
    print("=" * 75)
    print("DIAGNOSTIC: Worst-case 3-adic Fourier rate c_inf")
    print("Question: does c_inf stabilize at c > 0 or drift to 0?")
    print(f"Samples per point: 10^7, Workers: 20")
    print(f"Frequency panel: xi = 2^k, k/n in [1.2, 1.8] (near log_23)")
    print("=" * 75)
    print(f"{'n':<4} | {'s':<4} | {'max|E[chi]|':<12} | {'-ln(mag)/n':<12} | {'noise floor':<12} | {'2^k?':<5} | {'time':<8}")
    print("-" * 75)
    
    rates = []
    
    for n, s in test_points:
        t0 = time.time()
        max_mag, max_xi, is_2k, noise_floor = run_diagnostic(n, s, 
            total_samples=10**7, num_workers=20)
        t1 = time.time()
        
        # Compute effective rate only if signal above noise
        if max_mag > noise_floor:
            rate = -math.log(max_mag) / n
            rate_str = f"{rate:.6f}"
        else:
            rate = None
            rate_str = "< floor"
        
        rates.append((n, max_mag, rate, noise_floor))
        
        print(f"{n:<4} | {s:<4} | {max_mag:.6e}   | {rate_str:<12} | {noise_floor:.2e}   | {'Yes' if is_2k else 'No':<5} | {t1-t0:.1f}s")
    
    print("=" * 75)
    print("\nDIAGNOSTIC SUMMARY:")
    print("-" * 50)
    for n, mag, rate, nf in rates:
        if rate is not None:
            print(f"  n={n:>3}: rate = {rate:.6f} nats/step" +
                  (f"  (signal/noise = {mag/nf:.1f}x)" if mag > nf else "  (AT NOISE FLOOR)"))
        else:
            print(f"  n={n:>3}: signal below noise floor")
    
    print("\nInterpretation:")
    valid = [(n, r) for n, _, r, _ in rates if r is not None]
    if len(valid) >= 2:
        r_first = valid[0][1]
        r_last = valid[-1][1]
        if r_last < r_first * 0.5:
            print("  [!] Rate is DRIFTING DOWN -- consistent with c_inf = 0 (subexponential)")
            print("  -> Fourier barrier of Tao is likely impassable")
            print("  -> Superpolynomial (Allikvere Thm B) is the ceiling of the method")
        elif r_last > r_first * 0.8:
            print("  [ok] Rate appears STABLE -- consistent with c_inf > 0 (exponential)")
            print("  -> Lemma 0 upgrade to power-law stabilization may be feasible")
        else:
            print("  ? Rate is INCONCLUSIVE -- need larger n or more samples")
    else:
        print("  Too few valid points for diagnostic")
