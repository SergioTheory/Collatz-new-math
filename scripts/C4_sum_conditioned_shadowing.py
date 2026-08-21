import numpy as np
from numba import njit, prange
import math
import time

@njit
def power_mod(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        base = (base * base) % mod
        exp = exp // 2
    return res

@njit
def mod_inverse(a, m):
    m0 = m
    y = 0
    x = 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        t = m
        m = a % m
        a = t
        t = y
        y = x - q * y
        x = t
    if x < 0:
        x = x + m0
    return x

@njit(parallel=True)
def compute_beta_S_parallel(d, S, M, h_array):
    K = 1 << M
    # mod_S bounds rho_w mod 2^{S+1}
    mod_S = 1 << (S + 1)
    inv3_d = mod_inverse(power_mod(3, d, mod_S), mod_S)
    
    num_h = len(h_array)
    total_real = np.zeros(num_h, dtype=np.float64)
    total_imag = np.zeros(num_h, dtype=np.float64)
    
    max_a1 = S - d + 1
    for a1 in prange(1, max_a1 + 1):
        sum_real = np.zeros(num_h, dtype=np.float64)
        sum_imag = np.zeros(num_h, dtype=np.float64)
        
        S_j = np.zeros(d + 1, dtype=np.int32)
        c_j = np.zeros(d + 1, dtype=np.int64)
        a_try = np.zeros(d + 1, dtype=np.int32)
        
        S_j[1] = a1
        c_j[1] = (1 << a1) % mod_S
        depth = 1
        a_try[1] = 1
        
        while depth >= 1:
            if depth == d - 1:
                a = S - S_j[depth]
                S_next = S
                c_next = (3 * c_j[depth] + (1 << S_next)) % mod_S
                
                term1 = 1 << S
                val = (term1 * inv3_d - c_next * inv3_d - 1) % mod_S
                # Correct handling for negative modulo in python vs C via bitwise modulo for power of 2
                # In Python and numba, % on positive power of 2 is fine. 
                # Wait, val can be negative? No, all terms are positive and we took % mod_S.
                rw = (val // 2) % K
                
                for i in range(num_h):
                    angle = -2.0 * math.pi * h_array[i] * rw / K
                    sum_real[i] += math.cos(angle)
                    sum_imag[i] += math.sin(angle)
                    
                depth -= 1
            else:
                rem_S = S - S_j[depth]
                rem_d = d - depth
                
                if a_try[depth] <= rem_S - rem_d + 1:
                    a = a_try[depth]
                    a_try[depth] += 1
                    
                    S_j[depth + 1] = S_j[depth] + a
                    c_next = (3 * c_j[depth] + (1 << S_j[depth + 1])) % mod_S
                    c_j[depth + 1] = c_next
                    
                    depth += 1
                    a_try[depth] = 1
                else:
                    depth -= 1
                    
        for i in range(num_h):
            total_real[i] += sum_real[i]
            total_imag[i] += sum_imag[i]
            
    return total_real, total_imag

def run_C4():
    print("--- C4: Sum-Conditioned Boundary-Layer Decay ---")
    
    d_vals = [8, 10, 12, 14, 16]
    C_window = 2.0
    h_array = np.array([h for h in range(1, 101, 2)], dtype=np.int64)
    
    results = []
    
    for d in d_vals:
        M = 2 * d
        window_size = int(C_window * math.sqrt(d * math.log(d)))
        
        S_start = max(d, 2 * d - window_size)
        S_end = min(M, 2 * d + window_size)
        
        print(f"\nEvaluating d={d}, M={M}, S window=[{S_start}, {S_end}]", flush=True)
        
        max_beta_S_global = 0.0
        max_h_global = 0
        max_S_global = 0
        
        t0 = time.time()
        for S in range(S_start, S_end + 1):
            total_real, total_imag = compute_beta_S_parallel(d, S, M, h_array)
            
            # Normalize by 2^{-S}
            beta_mags = np.sqrt(total_real**2 + total_imag**2) / (2.0**S)
            
            max_idx = np.argmax(beta_mags)
            max_beta = beta_mags[max_idx]
            max_h = h_array[max_idx]
            
            if max_beta > max_beta_S_global:
                max_beta_S_global = max_beta
                max_h_global = max_h
                max_S_global = S
                
        t1 = time.time()
        print(f"  Max |beta_{{d,M,S}}(h)| = {max_beta_S_global:.6e} at S={max_S_global}, h={max_h_global}", flush=True)
        print(f"  Time taken: {t1 - t0:.2f} seconds", flush=True)
        results.append((d, max_beta_S_global))
        
    print("\nSummary of Conditional Maxima:")
    for d, val in results:
        print(f"  d={d:2d}: {val:.6e}")
        
    if len(results) >= 2:
        ratio = results[-1][1] / results[-2][1]
        print(f"\nDecay ratio from d={results[-2][0]} to d={results[-1][0]}: {ratio:.4f}")
        if ratio < 0.95:
            print("Verdict: PASS. Strong sum-conditioned decay observed. Positivity inequality is applicable!")
        else:
            print("Verdict: FAIL. Conditional max is ~O(1). Hypothesis C4 is refuted.")

if __name__ == '__main__':
    run_C4()
