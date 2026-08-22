import sys
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

def simulate_batch(args):
    n, xi, eps, num_paths = args
    max_j = n // 2
    
    rhos = []
    white_counts = []
    b3_counts = []
    
    for _ in range(num_paths):
        l = 0
        white = 0
        b3 = 0
        for j in range(1, max_j + 1):
            b = geom2() + geom2()
            l += b
            if b == 3:
                b3 += 1
                if theta_dist(j, l, n, xi) > eps:
                    white += 1
        if b3 > 0:
            rhos.append(white / float(b3))
            white_counts.append(white)
            b3_counts.append(b3)
            
    rhos = np.array(rhos)
    return {
        'min_rho': float(np.min(rhos)) if len(rhos) > 0 else 1.0,
        'mean_rho': float(np.mean(rhos)) if len(rhos) > 0 else 1.0,
        'p01_rho': float(np.percentile(rhos, 1)) if len(rhos) > 0 else 1.0,
        'p001_rho': float(np.percentile(rhos, 0.1)) if len(rhos) > 0 else 1.0,
        'zero_frac': float(np.mean(rhos == 0.0)) if len(rhos) > 0 else 0.0,
        'avg_white': float(np.mean(white_counts)) if len(white_counts) > 0 else 0.0,
        'avg_b3': float(np.mean(b3_counts)) if len(b3_counts) > 0 else 0.0,
    }

def main():
    print("=== Deep n Scaling for Front C (n=30..100) ===", flush=True)
    eps = 0.02
    ns = [20, 30, 40, 50, 60, 80, 100]
    xis = [1, 2, 4, 5, 7, 8]
    paths_per_task = 20000
    
    print(f"Epsilon = {eps}, Paths per (n, xi) = {paths_per_task}\n", flush=True)
    print(f"{'n':<4} | {'global min_rho':<15} | {'mean_rho':<10} | {'p01_rho':<10} | {'p001_rho':<10} | {'zero_frac':<12} | {'avg_b3':<8}", flush=True)
    print("-" * 80, flush=True)
    
    with ProcessPoolExecutor(max_workers=28) as executor:
        for n in ns:
            tasks = [(n, xi, eps, paths_per_task) for xi in xis]
            results = list(executor.map(simulate_batch, tasks))
            
            min_rhos = [r['min_rho'] for r in results]
            overall_min = min(min_rhos)
            mean_r = np.mean([r['mean_rho'] for r in results])
            p01_r = np.mean([r['p01_rho'] for r in results])
            p001_r = np.mean([r['p001_rho'] for r in results])
            zero_frac = np.mean([r['zero_frac'] for r in results])
            avg_b3 = np.mean([r['avg_b3'] for r in results])
            
            print(f"{n:<4} | {overall_min:<15.4f} | {mean_r:<10.4f} | {p01_r:<10.4f} | {p001_r:<10.4f} | {zero_frac:<12.6f} | {avg_b3:<8.2f}", flush=True)

if __name__ == '__main__':
    main()
