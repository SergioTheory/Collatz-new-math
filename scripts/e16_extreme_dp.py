import numpy as np
import time
from numba import njit
import math

@njit
def fast_dp(M, phase_shift, base_phase, final_phase):
    Z = np.zeros((M, M), dtype=np.complex128)
    Z[0, 0] = np.exp(-2j * np.pi * base_phase)
    
    for j in range(1, M):
        running_sum = 0j
        for S in range(1, M):
            running_sum += Z[S-1, j-1]
            if S >= j:
                Z[S, j] = np.exp(-2j * np.pi * phase_shift[S, j]) * running_sum
                
    total_I = 0j
    for d in range(1, M + 1):
        sum_Z = 0j
        for S in range(d-1, M):
            sum_Z += Z[S, d-1]
        total_I += np.exp(2j * np.pi * final_phase[d]) * sum_Z
        
    return total_I

def get_phase_float(val, M):
    # compute val / 2**(M+1) as float64
    shift = (M + 1) - 53
    if shift > 0:
        return float(val >> shift) / (1 << 53)
    else:
        return float(val) / (1 << (M + 1))

def compute_I(M, h):
    mod_exact = 1 << (M + 1)
    mask = mod_exact - 1
    
    inv3_arr = [pow(3, -d, mod_exact) for d in range(M + 2)]
    
    phase_shift = np.zeros((M, M), dtype=np.float64)
    for j in range(1, M):
        val = (h * inv3_arr[j+1] * (1 << j)) & mask
        for S in range(j, M):
            phase_shift[S, j] = get_phase_float(val, M)
            val = (val << 1) & mask
            
    base_phase = get_phase_float((h * inv3_arr[1]) & mask, M)
    
    final_phase = np.zeros(M + 1, dtype=np.float64)
    for d in range(1, M + 1):
        val = (h * ((1 << M) * inv3_arr[d] - 1)) & mask
        final_phase[d] = get_phase_float(val, M)
        
    return fast_dp(M, phase_shift, base_phase, final_phase)

def main():
    print("=== Asymptotic DP for Extreme M ===")
    
    # Warmup Numba
    compute_I(10, 1)
    
    M_list = [100, 500, 1000, 2000, 5000, 10000]
    
    import sys
    for h in [1]:
        print(f"\n--- Frequency h = {h} ---")
        prev_log_I = None
        prev_log_W = None
        
        for M in M_list:
            t0 = time.time()
            I_val = compute_I(M, h)
            t1 = time.time()
            
            mag = abs(I_val)
            
            # W can overflow float64, use math.log2 directly on magnitude
            log_I = math.log2(mag) if mag > 0 else 0
            log_W = M - 1
            
            theta_global = log_I / log_W if log_W > 0 else 0
            
            local_theta = 0
            if prev_log_I is not None:
                local_theta = (log_I - prev_log_I) / (log_W - prev_log_W)
                
            prev_log_I = log_I
            prev_log_W = log_W
            
            print(f"M={M:5d} | log2(W)={log_W:5d} | log2(|I|) = {log_I:8.2f} | theta_global = {theta_global:.5f} | theta_local = {local_theta:.5f} | time = {t1-t0:.3f}s")
            sys.stdout.flush()

if __name__ == '__main__':
    main()
