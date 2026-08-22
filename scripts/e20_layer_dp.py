import numpy as np
import math
import sys
from numba import njit
import time
from multiprocessing import Pool
import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

@njit(nogil=True, cache=True)
def fast_dp_layers(M, X_u64, base_phase, final_phase):
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
                B = M - S - 52
                if B >= 0:
                    L = B // 64
                    O = B % 64
                    limb0 = X_u64[j+1, L]
                    if O <= 11:
                        bits = (limb0 >> O) & 0x1FFFFFFFFFFFFF
                    else:
                        limb1 = X_u64[j+1, L + 1]
                        bits = ((limb0 >> O) | (limb1 << (64 - O))) & 0x1FFFFFFFFFFFFF
                    phase_f = float(bits) / (1 << 53)
                else:
                    avail = M - S + 1
                    limb0 = X_u64[j+1, 0]
                    bits = limb0 & ((1 << avail) - 1)
                    phase_f = float(bits) / (1 << avail)
                    
                Z_curr[S] = np.exp(-2j * np.pi * phase_f) * running_sum
                
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
        
    return I_mantissas, I_exponents

def compute_I_layers(M, h):
    mod_exact = 1 << (M + 1)
    mask = mod_exact - 1
    
    num_u64 = (M + 1 + 63) // 64
    X_u64 = np.zeros((M + 2, num_u64), dtype=np.uint64)
    
    inv3 = pow(3, -1, mod_exact)
    curr = (h * inv3) % mod_exact
    
    final_phase = np.zeros(M + 1, dtype=np.float64)
    
    inv3_d = inv3
    for d in range(1, M + 2):
        b = curr.to_bytes(num_u64 * 8, 'little')
        X_u64[d] = np.frombuffer(b, dtype=np.uint64)
        
        if d <= M:
            val = (h * ((1 << M) * inv3_d - 1)) & mask
            shift = (M + 1) - 53
            if shift > 0:
                final_phase[d] = float(val >> shift) / (1 << 53)
            else:
                final_phase[d] = float(val) / (1 << (M + 1))
                
        curr = (curr * inv3) % mod_exact
        inv3_d = (inv3_d * inv3) % mod_exact
        
    val = (h * pow(3, -1, mod_exact)) & mask
    shift = (M + 1) - 53
    if shift > 0:
        base_phase = float(val >> shift) / (1 << 53)
    else:
        base_phase = float(val) / (1 << (M + 1))
        
    return fast_dp_layers(M, X_u64, base_phase, final_phase)

def log2_binom(n, k):
    if k < 0 or k > n:
        return -float('inf')
    if k == 0 or k == n:
        return 0.0
    # Use sum of log2
    # log2(n!) - log2(k!) - log2((n-k)!)
    res = 0.0
    for i in range(1, k + 1):
        res += math.log2(n - i + 1) - math.log2(i)
    return res

def worker(M):
    t0 = time.time()
    I_mantissas, I_exponents = compute_I_layers(M, 1)
    t1 = time.time()
    
    # Analyze layers
    max_theta = -float('inf')
    max_d = -1
    
    results_d = []
    
    for d in range(1, M + 1):
        mag = abs(I_mantissas[d])
        if mag == 0:
            continue
        log2_I = math.log2(mag) + I_exponents[d]
        log2_W = log2_binom(M - 1, d - 1)
        
        if log2_W > 10: # Only care about macroscopic layers
            theta = log2_I / log2_W
            results_d.append((d, log2_W, log2_I, theta))
            if theta > max_theta:
                max_theta = theta
                max_d = d
                
    return (M, max_theta, max_d, t1 - t0, results_d)

def main():
    print("=== LAYER-WISE ASYMPTOTIC SWEEP ===", flush=True)
    compute_I_layers(10, 1) # Warmup Numba
    
    M_list = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    total = len(M_list)
    print(f"Total M values to test: {total}", flush=True)
    
    cores = min(10, len(M_list))
    
    with open("e20_results.txt", "w") as f:
        f.write("M,max_theta,max_d,time_s\n")
        
        with Pool(cores) as pool:
            for i, res in enumerate(pool.imap_unordered(worker, M_list)):
                M, max_theta, max_d, dt, _ = res
                f.write(f"{M},{max_theta:.6f},{max_d},{dt:.3f}\n")
                f.flush()
                print(f"M={M:5d} | Max Theta = {max_theta:.6f} at d={max_d}", flush=True)

if __name__ == '__main__':
    main()
