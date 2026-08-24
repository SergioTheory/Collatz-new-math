"""
Experiment D2: Survival set dimension drop curve
Evaluates the fractal dimensions (box and Assouad) of the survival set E_{N_0}
at an intermediate number of blocks k (before it drops to 0).
"""
import numpy as np
from numba import njit, prange
import time

@njit
def collatz_step(x):
    x = 3 * x + 1
    while x % 2 == 0:
        x //= 2
    return x

@njit(parallel=True)
def get_survivors(M, barrier, d, blocks):
    n_odd = 1 << (M - 1)
    surv = np.zeros(n_odd, dtype=np.bool_)
    
    for i in prange(n_odd):
        N = 2 * i + 1
        x = N
        ok = True
        for k in range(blocks):
            for step in range(d):
                x = collatz_step(x)
                if x <= barrier:
                    ok = False
                    break
            if not ok:
                break
        surv[i] = ok
    return surv

def analyze_structure(surv, M):
    n_odd = len(surv)
    current = surv.copy()
    box_counts = [np.sum(current)]
    
    for scale in range(M - 2, -1, -1):
        current = current[0::2] | current[1::2]
        box_counts.append(np.sum(current))
        
    box_counts = box_counts[::-1]
    d_box = np.log2(box_counts[-1]) / (M - 1) if box_counts[-1] > 0 else 0
    
    W = min(6, M-1)
    max_dim = 0.0
    window_size = 2**W
    
    idx = np.where(surv)[0]
    if len(idx) > 0:
        for i in range(0, n_odd, window_size):
            count = np.sum(surv[i:i+window_size])
            if count > 0:
                dim = np.log2(count) / W
                if dim > max_dim:
                    max_dim = dim
                    
    return d_box, max_dim

def main():
    print("Experiment D2: Dimension drop curve for E_{N_0}")
    print("Barrier N_0 = 2^{B-2}, block d=10, k = 0.8 * k*(B)")
    print(f"{'B':>3} | {'k':>3} | {'Surv count':>12} | {'d_box':>8} | {'d_A (thick)':>12} | {'T3 pred':>8}")
    print("-" * 65)
    
    # k*(B) from Exp 2
    k_stars = {20: 13, 22: 14, 24: 19, 26: 23, 28: 24, 30: 25}
    
    d = 10
    
    for B in [20, 22, 24, 26]:
        barrier = 1 << (B - 2)
        k_star = k_stars[B]
        k = int(0.8 * k_star)
        
        t0 = time.time()
        surv = get_survivors(B, barrier, d, k)
        d_box, d_A = analyze_structure(surv, B)
        elapsed = time.time() - t0
        
        # T3 prediction (approximate, since delta_1 < 0 we just output empirical)
        print(f"{B:3d} | {k:3d} | {np.sum(surv):12d} | {d_box:8.4f} | {d_A:12.4f} | {'-':>8}  ({elapsed:.1f}s)")

if __name__ == "__main__":
    main()
