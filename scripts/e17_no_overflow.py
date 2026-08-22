import numpy as np
import time
from numba import njit
import math
import sys

@njit
def fast_dp_no_overflow(M, phase_shift, base_phase, final_phase):
    Z_prev = np.zeros(M, dtype=np.complex128)
    Z_prev[0] = np.exp(-2j * np.pi * base_phase)
    
    I_mantissas = np.zeros(M + 1, dtype=np.complex128)
    I_exponents = np.zeros(M + 1, dtype=np.float64)
    
    current_exp = 0.0
    
    for j in range(1, M + 1):
        sum_Z = 0j
        for S in range(j - 1, M):
            sum_Z += Z_prev[S]
        
        I_mantissas[j] = np.exp(2j * np.pi * final_phase[j]) * sum_Z
        I_exponents[j] = current_exp
        
        if j == M:
            break
            
        Z_curr = np.zeros(M, dtype=np.complex128)
        running_sum = 0j
        for S in range(1, M):
            running_sum += Z_prev[S - 1]
            if S >= j:
                Z_curr[S] = np.exp(-2j * np.pi * phase_shift[S, j]) * running_sum
                
        max_mag = 0.0
        for S in range(M):
            mag = abs(Z_curr[S])
            if mag > max_mag:
                max_mag = mag
                
        if max_mag > 1e100:
            Z_curr /= 1e100
            current_exp += math.log2(1e100)
        elif max_mag < 1e-100 and max_mag > 0:
            Z_curr *= 1e100
            current_exp -= math.log2(1e100)
            
        Z_prev = Z_curr
        
    max_e = np.max(I_exponents)
    total_sum = 0j
    for d in range(1, M + 1):
        scale = 2.0 ** (I_exponents[d] - max_e)
        total_sum += I_mantissas[d] * scale
        
    final_mag = abs(total_sum)
    final_log2 = math.log2(final_mag) + max_e if final_mag > 0 else 0.0
    return final_log2

def get_phase_float(val, M):
    shift = (M + 1) - 53
    if shift > 0:
        return float(val >> shift) / (1 << 53)
    else:
        return float(val) / (1 << (M + 1))

def compute_I_log(M, h):
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
        
    return fast_dp_no_overflow(M, phase_shift, base_phase, final_phase)

def main():
    print("=== Asymptotic DP No Overflow ===")
    
    compute_I_log(10, 1)
    
    M_list = list(range(52, 102, 2))
    
    for h in [1]:
        print(f"\n--- Frequency h = {h} ---")
        prev_log_I = None
        prev_log_W = None
        
        for M in M_list:
            t0 = time.time()
            log_I = compute_I_log(M, h)
            t1 = time.time()
            
            log_W = M - 1
            theta_global = log_I / log_W if log_W > 0 else 0
            
            local_theta = 0
            if prev_log_I is not None:
                local_theta = (log_I - prev_log_I) / (log_W - prev_log_W)
                
            prev_log_I = log_I
            prev_log_W = log_W
            
            print(f"M={M:2d} | log2(W)={log_W:2d} | log2(|I|) = {log_I:7.3f} | theta_global = {theta_global:.5f} | theta_local = {local_theta:.5f}")
            sys.stdout.flush()

if __name__ == '__main__':
    main()
