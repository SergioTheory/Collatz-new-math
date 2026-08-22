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

def compute_I(M, h):
    mod_exact = 1 << (M + 1)
    
    inv3_arr = [pow(3, -d, mod_exact) for d in range(M + 2)]
    
    phase_shift = np.zeros((M, M), dtype=np.float64)
    for j in range(1, M):
        for S in range(j, M):
            val = (h * inv3_arr[j+1] * (1 << S)) % mod_exact
            phase_shift[S, j] = val / mod_exact
            
    base_phase = (h * inv3_arr[1]) % mod_exact / mod_exact
    
    final_phase = np.zeros(M + 1, dtype=np.float64)
    for d in range(1, M + 1):
        val = (h * ((1 << M) * inv3_arr[d] - 1)) % mod_exact
        final_phase[d] = val / mod_exact
        
    return fast_dp(M, phase_shift, base_phase, final_phase)

def main():
    print("=== Asymptotic DP for Low-Frequency Cancellation ===")
    
    # Warmup Numba
    compute_I(10, 1)
    
    M_list = list(range(20, 101, 10)) + [150, 200, 300, 400, 500, 1000]
    
    for h in [1, 2, 3]:
        print(f"\n--- Frequency h = {h} ---")
        prev_log_I = None
        prev_log_W = None
        
        for M in M_list:
            t0 = time.time()
            I_val = compute_I(M, h)
            t1 = time.time()
            
            mag = abs(I_val)
            W = 2**(M-1)
            
            # W can overflow float64 if M > 1024. For M=1000, 2^999 is ~ 10^300, fits in float64.
            log_I = math.log2(mag) if mag > 0 else 0
            log_W = M - 1
            
            theta_global = log_I / log_W if log_W > 0 else 0
            
            local_theta = 0
            if prev_log_I is not None:
                local_theta = (log_I - prev_log_I) / (log_W - prev_log_W)
                
            prev_log_I = log_I
            prev_log_W = log_W
            
            print(f"M={M:4d} | W=2^{M-1:<4d} | |I| = 2^{log_I:.2f} | theta_global = {theta_global:.4f} | theta_local = {local_theta:.4f} | time = {t1-t0:.3f}s")

if __name__ == '__main__':
    main()
