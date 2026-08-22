import numpy as np
import sys
import time

def compute_I_h(M, h):
    K = 1 << M
    K2 = 1 << (M + 1)
    total_sum = 0j
    pow3 = [pow(3, i, K2) for i in range(M+1)]
    pow3_inv = [pow(pow3[i], -1, K2) for i in range(M+1)]
    
    for d in range(1, M + 1):
        a = (h * pow3_inv[d]) % K2
        
        inv3_K2 = pow(3, -1, K2)
        base_num = ((1 << M) * pow3_inv[d] - inv3_K2 - 1) % K2
        
        base_phase = (h * (base_num // 2)) % K
        base_phase_float = 2 * np.pi * base_phase / float(K)
        
        dp = [0j] * (M + 1)
        dp[0] = 1.0 + 0j
        
        for j in range(1, d):
            next_dp = [0j] * (M + 1)
            xi_j_num = (-a * pow3[d - 1 - j]) % K2
            
            prefix_sum = 0j
            for S in range(j, M - (d - j) + 1):
                prefix_sum += dp[S - 1]
                p2 = (1 << S) % K2
                phase_num = (xi_j_num * p2) % K2
                phase = 2 * np.pi * (phase_num // 2) / float(K)
                next_dp[S] = prefix_sum * np.exp(1j * phase)
            dp = next_dp
            
        prefix_sum = 0j
        for S in range(d - 1, M):
            prefix_sum += dp[S]
        total_sum += prefix_sum * np.exp(1j * base_phase_float)
        
    return total_sum

def main():
    if len(sys.argv) > 1:
        M_list = [int(arg) for arg in sys.argv[1:]]
    else:
        M_list = [22, 30, 40, 50, 60]
        
    h_list = [1, 3, 5]
    
    print("=== DP Fourier Scaling for Large M ===")
    
    for M in M_list:
        W = 1 << (M - 1)
        sqrt_W = np.sqrt(W)
        print(f"\nM = {M} | W = {W}")
        t0 = time.time()
        for h in h_list:
            res = compute_I_h(M, h)
            mag = abs(res)
            ratio = mag / sqrt_W
            print(f"  h = {h}: |I({h})| = {mag:.2f} | |I({h})|/sqrt(W) = {ratio:.4f}")
        t1 = time.time()
        print(f"Time for M={M}: {t1 - t0:.2f}s")

if __name__ == '__main__':
    main()
