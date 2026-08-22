import numpy as np
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import time
from numba import njit
import math
import sys
from multiprocessing import Pool

@njit(nogil=True, cache=True)
def fast_dp_on_the_fly(M, X_u64, base_phase, final_phase):
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
        
    max_e = np.max(I_exponents)
    total_sum = 0j
    for d in range(1, M + 1):
        scale = 2.0 ** (I_exponents[d] - max_e)
        total_sum += I_mantissas[d] * scale
        
    final_mag = abs(total_sum)
    final_log2 = math.log2(final_mag) + max_e if final_mag > 0 else 0.0
    return final_log2

def compute_I_log_massive(M, h):
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
        
    return fast_dp_on_the_fly(M, X_u64, base_phase, final_phase)

def worker(M):
    t0 = time.time()
    log_I = compute_I_log_massive(M, 1)
    t1 = time.time()
    log_W = M - 1
    theta = log_I / log_W if log_W > 0 else 0
    return (M, log_I, theta, t1 - t0)

def main():
    print("=== MASSIVE ASYMPTOTIC SWEEP ===", flush=True)
    compute_I_log_massive(10, 1) # Warmup Numba
    
    M_list = list(range(10000, 100001, 1000))
    total = len(M_list)
    print(f"Total M values to test: {total}", flush=True)
    
    cores = 20
    print(f"Using {cores} processes (limited by 30GB RAM)", flush=True)
    
    results = []
    
    with open("e19_results.txt", "w") as f:
        f.write("M,log_W,log_I,theta,time_s\n")
        
        with Pool(cores) as pool:
            for i, res in enumerate(pool.imap_unordered(worker, M_list)):
                M, log_I, theta, dt = res
                results.append(res)
                
                f.write(f"{M},{M-1},{log_I:.3f},{theta:.6f},{dt:.3f}\n")
                
                if (i + 1) % 100 == 0 or (i + 1) == total:
                    f.flush()
                    max_res = max(results, key=lambda x: x[2])
                    print(f"[{i+1}/{total}] Processed. Max theta so far: M={max_res[0]} -> {max_res[2]:.6f}")
                    sys.stdout.flush()
                    
    results.sort(key=lambda x: x[2], reverse=True)
    print("\n--- TOP 10 THETA VALUES ---")
    for res in results[:10]:
        M, log_I, theta, dt = res
        print(f"M={M:5d} | theta = {theta:.6f} | log_I = {log_I:.2f}")

if __name__ == '__main__':
    main()
