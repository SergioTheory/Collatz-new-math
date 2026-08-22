"""
Per-j black probability: measure P(black | b_j=3) separately for each j.
This reveals where the Fourier mixing kicks in and where it doesn't.
If P(black) ≈ 2*eps uniformly for ALL j, anti-concentration works globally.
If P(black) deviates for small j, the argument only covers the tail.
"""
import random
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor

def theta_dist(j, l, n, xi):
    M = 3**n
    inv2 = (M + 1) // 2
    two_inv = pow(inv2, l - 1, M)
    r = (xi * pow(3, 2*j - 2, M) * two_inv) % M
    x = r / float(M)
    return min(x, 1.0 - x)

def geom2():
    k = 1
    while random.random() > 0.5:
        k += 1
    return k

def per_j_stats(args):
    n, xi, eps, num_paths = args
    max_j = n // 2
    # For each j: count (total_b3, black_b3)
    total_b3 = np.zeros(max_j + 1, dtype=np.int64)
    black_b3 = np.zeros(max_j + 1, dtype=np.int64)
    
    for _ in range(num_paths):
        l = 0
        for j in range(1, max_j + 1):
            b = geom2() + geom2()
            l += b
            if b == 3:
                total_b3[j] += 1
                if theta_dist(j, l, n, xi) <= eps:
                    black_b3[j] += 1
    
    return total_b3, black_b3

def main():
    print("=== Per-j Black Probability P(black | b_j=3) ===\n", flush=True)
    
    eps = 0.05
    num_paths = 100000
    
    configs = [
        (20, 1), (20, 5),
        (40, 1), (40, 7),
        (60, 1),
        (80, 1),
        (100, 1),
    ]
    
    print(f"eps = {eps}, theory P(black) = 2*eps = {2*eps:.3f}\n", flush=True)
    
    with ProcessPoolExecutor(max_workers=28) as executor:
        tasks = [(n, xi, eps, num_paths) for n, xi in configs]
        results = list(executor.map(per_j_stats, tasks))
    
    for (n, xi), (tot, blk) in zip(configs, results):
        max_j = n // 2
        print(f"\n--- n={n}, xi={xi} ---", flush=True)
        print(f"  Theory: 2*eps = {2*eps:.4f}", flush=True)
        print(f"  Group size N_j = 2*3^(n-2j+1), spectral gap ~ 4pi^2/N_j^2", flush=True)
        print(f"  {'j':<5} {'N_j':<12} {'gap':<12} {'#b3':<8} {'#black':<8} {'P(black)':<10} {'dev from 2eps':<14}", flush=True)
        print(f"  {'-'*75}", flush=True)
        
        for j in range(1, max_j + 1):
            k_j = n - 2*j + 2
            if k_j > 0:
                N_j = 2 * 3**(k_j - 1)
            else:
                N_j = 2
            
            gap = 4 * math.pi**2 / (N_j**2) if N_j > 1 else 1.0
            gap = min(gap, 1.0)
            
            t = int(tot[j])
            b = int(blk[j])
            if t > 0:
                p_black = b / t
                dev = p_black - 2*eps
                marker = "  <<<" if abs(dev) > 0.03 else ""
                print(f"  {j:<5} {N_j:<12} {gap:<12.6f} {t:<8} {b:<8} {p_black:<10.4f} {dev:<+14.4f}{marker}", flush=True)
            else:
                print(f"  {j:<5} {N_j:<12} {gap:<12.6f} {t:<8} {'N/A':<8}", flush=True)

if __name__ == '__main__':
    main()
