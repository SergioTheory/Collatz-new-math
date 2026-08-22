import numpy as np
import time
from numba import njit

@njit
def power_mod(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1: res = (res * base) % mod
        base = (base * base) % mod
        exp = exp // 2
    return res

@njit
def compute_cocycle_norm_fast(d_max, H):
    a_max = 50
    S_max = d_max * a_max
    
    V = np.zeros(S_max, dtype=np.complex128)
    V[0] = 1.0 + 0j
    
    norms = np.zeros(d_max)
    
    halves = np.zeros(a_max + 1)
    for a in range(a_max + 1):
        halves[a] = 0.5 ** a
        
    for j in range(1, d_max + 1):
        next_V = np.zeros(S_max, dtype=np.complex128)
        
        factor = (H * power_mod(3, d_max - j, 65536)) % 65536
        
        # Max S reached in previous steps is j * a_max
        # But to be safe, compute up to S_max
        current_max_S = j * a_max
        
        for S in range(1, current_max_S):
            sum_val = 0j
            for a in range(1, min(S, a_max) + 1):
                sum_val += V[S - a] * halves[a]
                
            phase_num = (factor * power_mod(2, S, 65536)) % 65536
            phase = 2 * np.pi * phase_num / 65536.0
            
            next_V[S] = sum_val * np.exp(-1j * phase)
            
        V = next_V
        
        current_norm = 0.0
        for S in range(current_max_S):
            current_norm += np.abs(V[S])
            
        norms[j-1] = current_norm
        
    return norms

def main():
    print("=== Fast Cocycle Norm Decay ===")
    
    # Compile numba
    compute_cocycle_norm_fast(10, 1)
    
    frequencies = [1, 3, 137, 1000]
    depths = [50, 100, 200, 400, 800]
    
    for H in frequencies:
        print(f"\n--- Frequency xi_0 = {H}/65536 ---")
        t0 = time.time()
        # Compute for max depth directly to get all norms
        max_d = max(depths)
        norms = compute_cocycle_norm_fast(max_d, H)
        
        for d in depths:
            norm_val = norms[d-1]
            decay = norm_val**(1.0/d)
            print(f"d = {d:3d}: final norm = {norm_val:.6e}, decay per step = {decay:.4f}")
        print(f"Time: {time.time()-t0:.2f}s")

if __name__ == '__main__':
    main()
