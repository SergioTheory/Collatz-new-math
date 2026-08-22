import numpy as np
import time
import math
from numba import njit

@njit
def power(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1: res = (res * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return res

@njit
def modInverse(a, m):
    m0 = m; y = 0; x = 1
    if m == 1: return 0
    while a > 1:
        q = a // m; t = m
        m = a % m; a = t
        t = y; y = x - q * y; x = t
    if x < 0: x += m0
    return x

@njit
def get_hist(M, B):
    mod_B = 1 << B
    mod_M1 = 1 << (M + 1)
    
    stack_d = np.zeros(M * M + 100, dtype=np.int64)
    stack_S = np.zeros(M * M + 100, dtype=np.int64)
    stack_cw = np.zeros(M * M + 100, dtype=np.int64)
    
    hist = np.zeros((M + 1, mod_B), dtype=np.int64)
    
    sp = 0
    stack_d[sp] = 0; stack_S[sp] = 0; stack_cw[sp] = 0
    sp += 1
    
    while sp > 0:
        sp -= 1
        d = stack_d[sp]; S = stack_S[sp]; c_w = stack_cw[sp]
        
        if S == M:
            p3_d = power(3, d, mod_M1)
            inv3 = modInverse(p3_d, mod_M1)
            diff = (1 << M) - c_w
            diff = diff % mod_M1
            if diff < 0: diff += mod_M1
            N_0 = (diff * inv3) % mod_M1
            y_0 = (power(3, d, mod_M1) * N_0 + c_w) >> M
            y_q = y_0 % mod_B
            if y_q < 0: y_q += mod_B
            hist[d, y_q] += 1
            continue
            
        for a in range(M - S, 0, -1):
            stack_d[sp] = d + 1
            stack_S[sp] = S + a
            stack_cw[sp] = 3 * c_w + (1 << S)
            sp += 1
            
    return hist

def main():
    B = 16
    Q = 10
    bucket_start = int(0.9 * (1 << B))
    if bucket_start % 2 == 0: bucket_start += 1
    
    print("=== Low-Frequency Mode Scaling ===")
    print(f"B = {B}, Q = {Q}, bucket_start = {bucket_start}")
    
    modes_to_test = [1, 2, 3, 4, 5]
    mod_B = 1 << B
    
    results = {h: [] for h in modes_to_test}
    W_vals = []
    
    for M in [30]:
        t0 = time.time()
        hist = get_hist(M, B)
        total_W = hist.sum()
        W_vals.append(total_W)
        
        print(f"\nM = {M} | W = {total_W} (DFS: {time.time()-t0:.2f}s)")
        
        # We only need the FFT for specific modes, but doing the whole thing is fast enough
        H = np.zeros((M + 1, mod_B), dtype=np.complex128)
        for d in range(M + 1):
            H[d] = np.conjugate(np.fft.fft(hist[d]))
            
        for h in modes_to_test:
            sum_I = 0j
            for d in range(M + 1):
                if hist[d].sum() == 0: continue
                phi = 0j
                step = (2 * pow(3, d, mod_B)) % mod_B
                for q in range(Q):
                    phi += np.exp(2j * np.pi * h * q * step / mod_B)
                sum_I += H[d, h] * phi
                
            I_h_mag = abs(sum_I)
            scaled = I_h_mag / math.sqrt(total_W)
            results[h].append(scaled)
            print(f"  h = {h}: |I({h})| = {I_h_mag:9.2f} | |I({h})|/sqrt(W) = {scaled:6.2f}")
            
    print("\n=== Scaling Summary (|I(h)| / sqrt(W)) ===")
    print(f"{'h':<4} | " + " | ".join([f"M={M}" for M in [30]]))
    print("-" * 50)
    for h in modes_to_test:
        row = f"{h:<4} | " + " | ".join([f"{val:4.2f}" for val in results[h]])
        print(row)

if __name__ == '__main__':
    main()
