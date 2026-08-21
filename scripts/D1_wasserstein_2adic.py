import numpy as np
import time
from numba import njit, prange

@njit
def apply_T(mu_curr, M):
    num_classes = 1 << (M - 1)
    mu_next = np.zeros(num_classes, dtype=np.float64)
    
    for idx in range(num_classes):
        prob = mu_curr[idx]
        if prob == 0:
            continue
        
        x = 2 * idx + 1
        val = (3 * x + 1) & ((1 << M) - 1)
        
        if val == 0:
            prob_split = prob / num_classes
            for i in range(num_classes):
                mu_next[i] += prob_split
        else:
            # find a = v_2(val)
            a = 0
            temp = val
            while (temp & 1) == 0:
                a += 1
                temp >>= 1
            
            y = temp & ((1 << (M - a)) - 1)
            step = 1 << (M - a - 1) # step for the index
            prob_split = prob / (1 << a)
            
            curr_idx = y // 2
            for _ in range(1 << a):
                mu_next[curr_idx] += prob_split
                curr_idx += step
                
    return mu_next

@njit
def compute_TV(mu_M, M):
    TV = np.zeros(M + 1, dtype=np.float64)
    num_M_classes = 1 << (M - 1)
    
    for k in range(1, M + 1):
        num_k_classes = 1 << (k - 1)
        mu_k = np.zeros(num_k_classes, dtype=np.float64)
        
        # map each class mod 2^M to its class mod 2^k
        # idx_M corresponds to x = 2*idx_M + 1
        # x mod 2^k is mapped to idx_k = (x % 2^k) // 2 = idx_M % 2^{k-1}
        mask_k = num_k_classes - 1
        for idx_M in range(num_M_classes):
            idx_k = idx_M & mask_k
            mu_k[idx_k] += mu_M[idx_M]
            
        tv_k = np.sum(np.abs(mu_k - 1.0 / num_k_classes))
        TV[k] = tv_k
        
    return TV

def run_wasserstein():
    print("--- D1: Tree-Wasserstein Metric Transport ---")
    M_vals = [16, 18, 20]
    
    for M in M_vals:
        print(f"\nEvaluating M = {M}")
        num_classes = 1 << (M - 1)
        mu = np.zeros(num_classes, dtype=np.float64)
        mu[0] = 1.0 # start entirely in class 1 mod 2^M
        
        # We apply T for d steps. 
        # To see stabilization, let's track d up to 24.
        # We will print at specific d values.
        d_targets = [4, 8, 12, 16, 20, 24]
        
        for d in range(1, max(d_targets) + 1):
            mu = apply_T(mu, M)
            
            if d in d_targets:
                TV = compute_TV(mu, M)
                
                # W1 distance
                W1 = 0.0
                for k in range(1, M + 1):
                    W1 += (2.0 ** (-k)) * TV[k]
                    
                print(f"  d = {d:2d} | W1 = {W1:.6e}")
                # Print TV profile for this d
                # To save space, print TV[k] for k in [1, 5, 10, 15, M]
                profile_k = [1, M//4, M//2, 3*M//4, M]
                profile_k = sorted(list(set(profile_k)))
                profile_str = ", ".join([f"TV_{k}={TV[k]:.4f}" for k in profile_k])
                print(f"           Profile: {profile_str}")

if __name__ == '__main__':
    run_wasserstein()
