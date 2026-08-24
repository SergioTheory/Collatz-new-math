"""
Experiment D: Porosity and Assouad dimension of the survival set
Diagnoses the geometric structure of E_{N_0} in the 2-adic space.
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
    """
    Returns a boolean array of size 2^{M-1}.
    True if the odd number N = 2*i + 1 in [0, 2^M)
    survives `blocks` chunks of `d` steps above `barrier`.
    """
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
    """
    Computes Porosity, Box-counting dimension, and Assouad dimension bounds.
    `surv` is a boolean array of size 2^{M-1} (representing odd numbers).
    """
    n_odd = len(surv)
    
    # 1. Porosity: max empty run / total size
    # We can find this by diffing indices of True
    idx = np.where(surv)[0]
    if len(idx) == 0:
        return 1.0, 0.0, 0.0
        
    gaps = np.diff(idx)
    max_gap = np.max(gaps) if len(gaps) > 0 else n_odd
    # Include edge gaps
    max_gap = max(max_gap, idx[0], n_odd - 1 - idx[-1])
    porosity = max_gap / n_odd
    
    # 2. Box-counting dimension (simplified: evaluating at all available scales)
    # A box of size 2^j (in terms of odds, it's 2^{j-1})
    # We check how many boxes of size 2^{j-1} contain at least one survivor.
    d_box_estimates = []
    # Assouad dim: max ratio of log(N(R)/N(r)) / log(R/r)
    d_A_estimates = []
    
    # To compute these efficiently, we can downsample the `surv` array.
    # surv_j[i] = surv_{j-1}[2i] | surv_{j-1}[2i+1]
    
    current = surv.copy()
    box_counts = [np.sum(current)] # scale M-1
    
    for scale in range(M - 2, -1, -1):
        # pair up adjacent elements
        current = current[0::2] | current[1::2]
        box_counts.append(np.sum(current))
        
    box_counts = box_counts[::-1] # now index j corresponds to scale j (box size 2^(M-1-j))
    
    # d_box ~ log2(box_counts[j]) / j
    # We use the finest scale available (j = M-1)
    d_box = np.log2(box_counts[-1]) / (M - 1) if box_counts[-1] > 0 else 0
    
    # Assouad dimension is roughly the maximum local density exponent.
    # We can approximate it by looking at the maximum number of children a box has
    # at various scales.
    # In base 2, Assouad dim <= 1. If it's 1, there's a fully populated ball somewhere.
    # Max boxes of size 2^{-k} inside a box of size 2^{-j} is 2^{k-j}.
    # The dimension is log2(max_count) / (k-j).
    # Since we are on a binary tree, if ANY node has both children surviving, 
    # the local dimension at that step is log2(2)/1 = 1.
    # A better proxy for Assouad is the "thickest" branch over multiple scales.
    
    # Let's compute the max density over a window of W scales.
    W = min(5, M-1)
    max_dim = 0.0
    
    # Count survivors in sliding windows
    # For a fixed node at scale j (size 2^{M-1-j}), how many survivors does it have at scale j+W?
    # We can just use a sliding sum on the original array.
    window_size = 2**W
    
    if len(idx) > 0:
        # sliding window sum of survivors
        # To avoid massive arrays, just check intervals of size 2^W
        for i in range(0, n_odd, window_size):
            count = np.sum(surv[i:i+window_size])
            if count > 0:
                dim = np.log2(count) / W
                if dim > max_dim:
                    max_dim = dim
                    
    d_A = max_dim
    return porosity, d_box, d_A

def main():
    print("Experiment D: Porosity and Dimensions of E_{N_0}")
    print("Computing exact 2-adic structural invariants.\n")
    
    d = 10
    
    print(f"{'B (scale)':>9} | {'Surv count':>12} | {'Porosity':>10} | {'d_box':>8} | {'d_A (thick)':>12}")
    print("-" * 60)
    
    for B in [20, 22, 24, 26]: # Keep it feasible for memory/time
        # In the paper, barrier is fixed or scales with B. Let's use N_0 = 1000
        barrier = 1000
        # How many blocks? Enough to filter out the noise.
        # k*(B) was ~B. Let's use blocks = B.
        blocks = B
        
        t0 = time.time()
        surv = get_survivors(B, barrier, d, blocks)
        
        por, d_box, d_A = analyze_structure(surv, B)
        elapsed = time.time() - t0
        
        print(f"{B:9d} | {np.sum(surv):12d} | {por:10.4f} | {d_box:8.4f} | {d_A:12.4f}  ({elapsed:.1f}s)")

if __name__ == "__main__":
    main()
