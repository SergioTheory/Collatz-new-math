"""
Experiment 2: k*(B) - minimum number of blocks until ALL B-bit survivors drop.

Purpose: Measure the growth rate of k*(B) to diagnose the Archimedean-2-adic wall.

Setup (consistent with T3 in the paper):
  - Start: all odd N in [2^{B-1}, 2^B)  (B-bit numbers)
  - Barrier: N_0 = 2^{B-2}  (half the starting range, gives room for initial steps)
  - Block: d = 10 accelerated odd Collatz steps
  - Survival: ALL d iterates within a block exceed N_0
  - k*(B): first k such that no starting N has survived k consecutive blocks

Interpretation:
  - If k*(B) grows sublinearly in B -> wall may be penetrable
  - If k*(B) grows linearly or faster -> wall is real

HARDWARE: E5-2696v3, 30 workers. Using numba parallel.
"""

import numpy as np
from numba import njit, prange
import time
import sys

@njit
def collatz_step(x):
    """One accelerated odd Collatz step: x -> (3x+1)/2^v"""
    x = 3 * x + 1
    while x % 2 == 0:
        x //= 2
    return x

@njit
def max_survival_blocks(N, barrier, d, max_k):
    """Count how many consecutive d-step blocks N survives above barrier."""
    x = N
    for k in range(max_k):
        for step in range(d):
            x = collatz_step(x)
            if x <= barrier:
                return k  # dropped during block k (0-indexed)
    return max_k  # survived all max_k blocks

@njit(parallel=True)
def count_survivors_per_k(B, d, max_k):
    lo = np.int64(1) << np.int64(B - 1)
    hi = np.int64(1) << np.int64(B)
    barrier = np.int64(1) << np.int64(B - 2)
    
    total_odd = (hi - lo) // 2
    counts = np.zeros(max_k + 1, dtype=np.int64)
    
    for idx in prange(total_odd):
        N = lo + 2 * idx + 1
        if N >= hi:
            continue
        k_survived = max_survival_blocks(N, barrier, d, max_k)
        if k_survived <= max_k:
            counts[k_survived] += 1
            
    return counts

def find_kstar_safe(B, d, max_k):
    # Get the full distribution
    counts = count_survivors_per_k(B, d, max_k)
    # The total number of starting points is sum(counts)
    total = np.sum(counts)
    
    # Calculate how many survived *at least* k blocks
    # counts[k] is the number that died EXACTLY at block k (survived k blocks)
    # So to survive >= k blocks, we sum counts[k:]
    # The maximum k for which survived_at_least_k > 0 is our k*
    
    survived_at_least_k = np.zeros(max_k + 1, dtype=np.int64)
    current_survivors = total
    
    kstar = 0
    for k in range(max_k + 1):
        survived_at_least_k[k] = current_survivors
        if current_survivors > 0:
            kstar = k
        current_survivors -= counts[k]
        
    return kstar, counts

def main():
    d = 10       # block size (accelerated steps)
    max_k = 200  # maximum blocks to simulate
    
    print("Experiment 2: k*(B) - survival block count")
    print(f"Block size d = {d}, barrier = 2^(B-2), max_k = {max_k}")
    print(f"{'B':>4} | {'#odd':>12} | {'k*':>6} | {'time(s)':>8} | {'k*/B':>8}")
    print("-" * 52)
    
    results = []
    
    # Warmup numba
    _ = count_survivors_per_k(16, d, 10)
    
    for B in range(18, 28):
        t0 = time.time()
        kstar, _ = find_kstar_safe(B, d, max_k)
        elapsed = time.time() - t0
        
        n_odd = (1 << (B-1)) // 2  # approximate
        
        print(f"{B:4d} | {n_odd:12d} | {kstar:6d} | {elapsed:8.2f} | {kstar/B:8.3f}")
        results.append((B, kstar, elapsed))
        
        sys.stdout.flush()
        
        if elapsed > 600:
            print(f"  (stopping: B={B} took {elapsed:.0f}s)")
            break
            
    print("\n\nSurvivor distribution for select B values:")
    for B in [20, 22, 24]:
        print(f"\n--- B = {B} ---")
        t0 = time.time()
        counts = count_survivors_per_k(B, d, min(max_k, 100))
        elapsed = time.time() - t0
        
        total = np.sum(counts)
        print(f"{'k':>4} | {'died at k':>12} | {'survived >=k':>14} | {'fraction':>10}")
        current_survivors = total
        for k in range(min(len(counts), 30)):
            frac = current_survivors / total if total > 0 else 0.0
            print(f"{k:4d} | {counts[k]:12d} | {current_survivors:14d} | {frac:10.6f}")
            if current_survivors == 0:
                break
            current_survivors -= counts[k]
            
        print(f"Time: {elapsed:.2f}s")
        
    print("\n\nSUMMARY")
    print("="*52)
    print(f"{'B':>4} | {'k*':>6} | {'k*/B':>8} | {'k*/sqrt(B)':>12}")
    print("-" * 36)
    for B, kstar, _ in results:
        print(f"{B:4d} | {kstar:6d} | {kstar/B:8.3f} | {kstar/np.sqrt(B):12.3f}")

if __name__ == "__main__":
    main()
