import numpy as np
import time
from numba import njit
import sys

@njit
def compute_hierarchical_data(M, K_list, h=1):
    # Enumerate all compositions of M.
    mod_val = 1 << (M - 1)
    K_max = max(K_list)
    num_K = len(K_list)
    
    # We will accumulate the Fourier sum for the full phase, and for the tail phases
    total_sum_full = 0j
    total_sums_tail = np.zeros(num_K, dtype=np.complex128)
    
    # Histogram of full c_w (only top 10 bits to avoid huge memory if M is large)
    hist_bits = min(16, M - 1)
    shift_bits = max(0, (M - 1) - hist_bits)
    hist_size = 1 << hist_bits
    hist = np.zeros(hist_size, dtype=np.int64)
    
    # Iterative DFS stack
    stack_d = np.zeros(M * M + 100, dtype=np.int32)
    stack_S = np.zeros(M * M + 100, dtype=np.int32)
    stack_cw = np.zeros(M * M + 100, dtype=np.int64)
    
    # For tail phase, we need to know the terms.
    # We can just keep an array of S_j for the current path
    stack_S_hist = np.zeros(M + 1, dtype=np.int32)
    
    sp = 0
    stack_d[sp] = 0
    stack_S[sp] = 0
    stack_cw[sp] = 0
    sp += 1
    
    # Precompute powers of 3 modulo 2^{M+1} to compute exact r_w
    mod_exact = 1 << (M + 1)
    pow3 = np.zeros(M + 1, dtype=np.int64)
    pow3[0] = 1
    for i in range(1, M + 1):
        pow3[i] = (pow3[i-1] * 3) % mod_exact
        
    def modInverse(a, m):
        m0 = m; y = 0; x = 1
        if m == 1: return 0
        while a > 1:
            q = a // m; t = m
            m = a % m; a = t
            t = y; y = x - q * y; x = t
        if x < 0: x += m0
        return x
        
    inv3_arr = np.zeros(M + 1, dtype=np.int64)
    for i in range(M + 1):
        inv3_arr[i] = modInverse(pow3[i], mod_exact)
    
    W = 0
    
    while sp > 0:
        sp -= 1
        d = stack_d[sp]
        S = stack_S[sp]
        c_w = stack_cw[sp]
        
        if S == M:
            W += 1
            
            # 1. Update histogram of c_w
            # Wait, c_w is computed iteratively as c_d = 3*c_{d-1} + 2^{S_{d-1}}.
            # This is exactly what stack_cw tracks!
            cw_mod = c_w % mod_val
            hist_idx = cw_mod >> shift_bits
            hist[hist_idx] += 1
            
            # 2. Exact full phase
            inv3 = inv3_arr[d]
            rho_w = ((1 << M) - c_w) % mod_exact
            if rho_w < 0: rho_w += mod_exact
            rho_w = (rho_w * inv3) % mod_exact
            r_w = (rho_w - 1) // 2
            
            phase_full = 2 * np.pi * h * r_w / (1 << M)
            total_sum_full += np.exp(1j * phase_full)
            
            # 3. Tail phases
            # c_w_tail is the sum of 3^{d-1-j} 2^{S_j} for S_j >= M - K
            for ki in range(num_K):
                K_val = K_list[ki]
                cw_tail = 0
                for j in range(d):
                    S_j = stack_S_hist[j]
                    if S_j >= M - K_val:
                        term = (pow3[d - 1 - j] * (1 << S_j)) % mod_exact
                        cw_tail = (cw_tail + term) % mod_exact
                        
                rho_w_tail = ((1 << M) - cw_tail) % mod_exact
                if rho_w_tail < 0: rho_w_tail += mod_exact
                rho_w_tail = (rho_w_tail * inv3) % mod_exact
                r_w_tail = (rho_w_tail - 1) // 2
                phase_tail = 2 * np.pi * h * r_w_tail / (1 << M)
                total_sums_tail[ki] += np.exp(1j * phase_tail)
                
            continue
            
        for a in range(M - S, 0, -1):
            stack_d[sp] = d + 1
            stack_S[sp] = S + a
            stack_cw[sp] = (3 * c_w + (1 << S)) % mod_exact
            stack_S_hist[d] = S
            sp += 1
            
    return W, total_sum_full, total_sums_tail, hist

def main():
    M_list = [20, 22, 24]
    K_list = np.array([2, 4, 6, 8, 10], dtype=np.int64)
    
    print("=== Hierarchical Phase Factorization ===")
    
    for M in M_list:
        print(f"\n--- M = {M} ---")
        t0 = time.time()
        W, sum_full, sums_tail, hist = compute_hierarchical_data(M, K_list, h=1)
        t1 = time.time()
        
        print(f"W = {W}, time = {t1-t0:.2f}s")
        print(f"Full Cancellation |I(1)|/sqrt(W) = {abs(sum_full)/np.sqrt(W):.4f}")
        
        for i, K in enumerate(K_list):
            print(f"Tail(K={K}) Cancellation |I_tail(1)|/sqrt(W) = {abs(sums_tail[i])/np.sqrt(W):.4f}")
            
        # Histogram stats
        hist_mean = W / len(hist)
        hist_var = np.var(hist)
        hist_std = np.sqrt(hist_var)
        print(f"Histogram of c_w (top 16 bits): mean = {hist_mean:.1f}, std = {hist_std:.1f}, max = {np.max(hist)}, min = {np.min(hist)}")
        
        if hist_std > 2 * np.sqrt(hist_mean):
            print("  -> DISTRIBUTION IS HIGHLY CLUSTERED")
        else:
            print("  -> DISTRIBUTION IS RELATIVELY UNIFORM (Poisson-like)")

if __name__ == '__main__':
    main()
