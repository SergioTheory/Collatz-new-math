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
    
    # Precompute inverses and powers to avoid doing it inside the loop
    # For a fixed S=M, we only need to map the endpoints
    # Wait, the endpoint y is y = Syr^d(N).
    # N is defined by 3^d N + c_w = 2^S (mod 2^{S+1})
    # y = (3^d N + c_w) / 2^S.
    # So y is exactly (3^d N + c_w) >> M
    
    # stack sizes bounded by M*M
    stack_d = np.zeros(M * M + 100, dtype=np.int64)
    stack_S = np.zeros(M * M + 100, dtype=np.int64)
    stack_cw = np.zeros(M * M + 100, dtype=np.int64)
    
    hist = np.zeros((M + 1, mod_B), dtype=np.float64)
    
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
            hist[d, y_q] += 1.0
            continue
            
        for a in range(M - S, 0, -1):
            stack_d[sp] = d + 1
            stack_S[sp] = S + a
            stack_cw[sp] = 3 * c_w + (1 << S)
            sp += 1
            
    return hist

def run_test(M, B):
    print(f"\n=== M={M}, B={B} ===")
    t0 = time.time()
    hist = get_hist(M, B)
    t1 = time.time()
    total_words = hist.sum()
    print(f"DFS computed {total_words} words in {t1-t0:.2f}s")
    
    # We want the unrestricted histogram
    hist_unrestricted = hist.sum(axis=0)
    
    # FFT
    t0 = time.time()
    fft_res = np.fft.fft(hist_unrestricted)
    t1 = time.time()
    print(f"FFT computed in {t1-t0:.2f}s")
    
    mags = np.abs(fft_res)
    mags_odd = mags[1::2]
    max_odd_idx = np.argmax(mags_odd)
    max_h = 2 * max_odd_idx + 1
    max_mag = mags_odd[max_odd_idx]
    
    normalized_max = max_mag / total_words
    
    print(f"Max Fourier Peak (odd h): h = {max_h}")
    print(f"Magnitude = {max_mag:.2f}")
    print(f"Normalized |Delta_b(h)| = {normalized_max:.6f}")
    print(f"Theoretical decay expectation 2^{{-B/2}} = {2**(-B/2):.6f}")
    print(f"Ratio = {normalized_max / (2**(-B/2)):.2f}")

def main():
    run_test(22, 22)
    run_test(24, 24)

if __name__ == "__main__":
    main()
