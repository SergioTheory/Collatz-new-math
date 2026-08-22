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
    M = 22
    B = 16
    Q = 10
    bucket_start = int(0.9 * (1 << B))
    if bucket_start % 2 == 0: bucket_start += 1
    
    print(f"=== E10 Fourier Diagnostics ===")
    print(f"M = {M}, B = {B}, Q = {Q}, bucket_start = {bucket_start}")
    
    t0 = time.time()
    hist = get_hist(M, B)
    total_W = hist.sum()
    print(f"DFS done in {time.time()-t0:.2f}s. Total W = {total_W}")
    
    mod_B = 1 << B
    
    # 1. Fourier decomposition
    H = np.zeros((M + 1, mod_B), dtype=np.complex128)
    for d in range(M + 1):
        # We need sum_y hist[y] e^{2pi i h y / N}
        H[d] = np.conjugate(np.fft.fft(hist[d]))
        
    c = np.zeros(mod_B, dtype=np.complex128)
    for h in range(1, mod_B):
        num = np.exp(-2j * np.pi * h * bucket_start / mod_B) - 1
        den = 1 - np.exp(-2j * np.pi * h / mod_B)
        c[h] = (num / den) / mod_B
        
    I_h = np.zeros(mod_B, dtype=np.complex128)
    for h in range(1, mod_B):
        sum_I = 0j
        for d in range(M + 1):
            if hist[d].sum() == 0: continue
            phi = 0j
            step = (2 * pow(3, d, mod_B)) % mod_B
            for q in range(Q):
                phi += np.exp(2j * np.pi * h * q * step / mod_B)
            sum_I += H[d, h] * phi
        I_h[h] = sum_I
        
    total_eps_h = c * I_h
    total_discrepancy = np.sum(total_eps_h).real
    print(f"Total discrepancy from Fourier sum: {total_discrepancy:.2f} (Expected: ~84379.00)")
    
    # 2. Top 20 modes
    magnitudes = np.abs(total_eps_h)
    # Ignore h=0 since total_eps_h[0] = 0
    sorted_h = np.argsort(magnitudes)[::-1]
    
    print("\n--- Top 20 modes by contribution magnitude ---")
    print(f"{'Rank':<5} | {'h':<6} | {'a = h*3^d mod 2^{B-1} (avg d)':<30} | {'|c(h)|':<8} | {'|I(h)|':<10} | {'|c(h)*I(h)|':<12} | {'Phase(c*I)':<10}")
    
    avg_d = sum(d * hist[d].sum() for d in range(M+1)) / total_W
    d_approx = int(round(avg_d))
    mod_B_half = 1 << (B - 1)
    
    for rank in range(20):
        h = sorted_h[rank]
        if h == 0 or magnitudes[h] < 1e-9: continue
        mag = magnitudes[h]
        phase = np.angle(total_eps_h[h], deg=True)
        
        a = (h * pow(3, d_approx, mod_B_half)) % mod_B_half
        if a > (mod_B_half // 2): a -= mod_B_half
        
        print(f"{rank+1:<5} | {h:<6} | {a:<30} | {abs(c[h]):.4f}   | {abs(I_h[h]):.2f}    | {mag:.2f}      | {phase:.1f}")
        
    # 3. Effective dimension and scaling
    total_mag_sum = np.sum(magnitudes)
    
    print(f"\n--- Residual Scaling Analysis ---")
    print(f"Initial Discrepancy: {total_discrepancy:.2f}")
    print(f"Naive sqrt(W) bound: {math.sqrt(total_W):.2f}\n")
    
    for K in [5, 20, 100, 1000]:
        top_k_h = sorted_h[:K]
        top_k_sum = np.sum(total_eps_h[top_k_h])
        top_k_mag = np.sum(magnitudes[top_k_h])
        rem = total_discrepancy - top_k_sum.real
        
        print(f"Top {K} modes:")
        print(f"  Sum of magnitudes: {top_k_mag:.2f} ({top_k_mag/total_mag_sum*100:.1f}% of total spectral mass)")
        print(f"  Real contribution: {top_k_sum.real:.2f} ({(abs(top_k_sum.real)/abs(total_discrepancy))*100:.1f}% of discrepancy)")
        print(f"  Discrepancy AFTER subtracting top {K}: {rem:.2f}")
        print(f"  Residual / sqrt(W): {abs(rem) / math.sqrt(total_W):.2f}\n")

if __name__ == '__main__':
    main()
