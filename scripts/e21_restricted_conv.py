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
def fast_dp_layers_h(M, X_u64, base_phase, final_phase):
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

def compute_I_layers_h(M, h):
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
        
    return fast_dp_layers_h(M, X_u64, base_phase, final_phase)

def log2_binom(n, k):
    if k < 0 or k > n: return -float('inf')
    if k == 0 or k == n: return 0.0
    res = 0.0
    for i in range(1, k + 1):
        res += math.log2(n - i + 1) - math.log2(i)
    return res

def worker_h(args):
    M, h_target, K_conv = args
    
    # We will compute unrestricted sums for h in [h_target - K_conv, h_target + K_conv]
    # And apply a window convolution.
    
    # Let bucket be [0, 0.1]. Indicator function Fourier coeffs:
    # c_k = int_0^{0.1} e^{-2pi i k x} dx = (1 - e^{-0.2 pi i k}) / (2 pi i k) if k != 0 else 0.1
    def c_k(k):
        if k == 0: return 0.1
        return (1.0 - np.exp(-2j * np.pi * k * 0.1)) / (2j * np.pi * k)
    
    unrestricted_results = {}
    for h in range(h_target - K_conv, h_target + K_conv + 1):
        if h == 0:
            unrestricted_results[h] = (np.ones(M+1, dtype=np.complex128), np.zeros(M+1)) # h=0 is trivial
        else:
            I_m, I_e = compute_I_layers_h(M, h)
            unrestricted_results[h] = (I_m, I_e)
            
    # Now convolve for each d
    restricted_m = np.zeros(M+1, dtype=np.complex128)
    restricted_e = np.zeros(M+1, dtype=np.float64)
    
    d_vals = [M//2 - 10, M//2, M//2 + 10]
    
    results = []
    
    for d in d_vals:
        sum_val = 0j
        max_e = -float('inf')
        for h in range(h_target - K_conv, h_target + K_conv + 1):
            if h == 0: continue
            I_m, I_e = unrestricted_results[h]
            max_e = max(max_e, I_e[d])
            
        for h in range(h_target - K_conv, h_target + K_conv + 1):
            if h == 0: continue
            I_m, I_e = unrestricted_results[h]
            k = h_target - h
            coeff = c_k(k)
            sum_val += I_m[d] * (2.0**(I_e[d] - max_e)) * coeff
            
        mag = abs(sum_val)
        if mag > 0:
            log_I = math.log2(mag) + max_e
            log_W = log2_binom(M-1, d-1)
            theta = log_I / log_W if log_W > 0 else 0
            results.append((d, log_W, log_I, theta))
            
    return (M, h_target, results)

def main():
    M = 500
    h_targets = [1, 2, 3]
    K_conv = 10
    
    args = [(M, h, K_conv) for h in h_targets]
    
    with Pool(3) as pool:
        for res in pool.imap_unordered(worker_h, args):
            M_val, h_val, d_res = res
            print(f"M={M_val}, h={h_val}")
            for r in d_res:
                d, log_W, log_I, theta = r
                print(f"  d={d}: theta={theta:.6f}")
                
if __name__ == '__main__':
    main()
