import numpy as np
import time
import math
from numba import njit, prange

@njit
def apply_T_cond(mu_curr, M, max_S):
    num_classes = 1 << (M - 1)
    mu_next = np.zeros((max_S + 1, num_classes), dtype=np.float64)
    
    for s in range(max_S + 1):
        for idx in range(num_classes):
            prob = mu_curr[s, idx]
            if prob == 0:
                continue
            
            x = 2 * idx + 1
            val = (3 * x + 1) & ((1 << M) - 1)
            
            if val == 0:
                # a >= M
                for k in range(max_S - s - M + 1):
                    a = M + k
                    prob_split = prob * (0.5 ** (k + 1)) / num_classes
                    for i in range(num_classes):
                        mu_next[s + a, i] += prob_split
            else:
                a = 0
                temp = val
                while (temp & 1) == 0:
                    a += 1
                    temp >>= 1
                
                if s + a <= max_S:
                    y = temp & ((1 << (M - a)) - 1)
                    step = 1 << (M - a - 1)
                    prob_split = prob / (1 << a)
                    
                    curr_idx = y // 2
                    for _ in range(1 << a):
                        mu_next[s + a, curr_idx] += prob_split
                        curr_idx += step
                        
    return mu_next

@njit
def compute_TV(mu_M, M):
    TV = np.zeros(M + 1, dtype=np.float64)
    num_M_classes = 1 << (M - 1)
    
    for k in range(1, M + 1):
        num_k_classes = 1 << (k - 1)
        mu_k = np.zeros(num_k_classes, dtype=np.float64)
        
        mask_k = num_k_classes - 1
        for idx_M in range(num_M_classes):
            idx_k = idx_M & mask_k
            mu_k[idx_k] += mu_M[idx_M]
            
        tv_k = np.sum(np.abs(mu_k - 1.0 / num_k_classes))
        TV[k] = tv_k
        
    return TV

def run_d4():
    print("--- D4: Conditional S-Layer Transport Diagnostics ---")
    M_vals = [16, 18, 20]
    
    for M in M_vals:
        print(f"\nEvaluating M = {M}")
        num_classes = 1 << (M - 1)
        d_target = M // 2
        
        max_S = M + 2
        mu = np.zeros((max_S + 1, num_classes), dtype=np.float64)
        mu[0, 0] = 1.0  # Start at x=1, S=0
        
        for d in range(1, d_target + 1):
            mu = apply_T_cond(mu, M, max_S)
            
        # Evaluate for specific S
        S_targets = [M - 2, M, M + 2]
        
        for S in S_targets:
            if S > max_S:
                continue
                
            mu_S = mu[S, :].copy()
            total_mass = np.sum(mu_S)
            
            if total_mass == 0:
                print(f"  d = {d_target}, S = {S} | Mass = 0")
                continue
                
            # Normalize conditional measure
            mu_S_norm = mu_S / total_mass
            
            TV = compute_TV(mu_S_norm, M)
            
            W1 = 0.0
            for k in range(1, M + 1):
                W1 += (2.0 ** (-k)) * TV[k]
                
            # Compute Entropy
            entropy = 0.0
            for p in mu_S_norm:
                if p > 0:
                    entropy -= p * math.log2(p)
                    
            max_entropy = M - 1
            entropy_deficit = max_entropy - entropy
            
            print(f"  d = {d_target:2d}, S = {S:2d} | W1 = {W1:.6f} | TV = {TV[M]:.6f} | Ent.Deficit = {entropy_deficit:.4f} bits")
            
            profile_k = [1, M//4, M//2, 3*M//4, M]
            profile_k = sorted(list(set(profile_k)))
            profile_str = ", ".join([f"TV_{k}={TV[k]:.4f}" for k in profile_k])
            print(f"           Profile: {profile_str}")

if __name__ == '__main__':
    run_d4()
