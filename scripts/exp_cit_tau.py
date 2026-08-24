"""
Experiment CIT: Cylinder-Interval Transversality (tau factor)
Measures the transversality factor tau(S) between 2-adic cylinders 
of low shift and an Archimedean interval I = [2^{B-1}, 2^B).
"""

import numpy as np
from numba import njit, prange
import time

@njit
def power_mod(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        base = (base * base) % mod
        exp //= 2
    return res

@njit
def mod_inverse(a, m):
    # m is power of 2, a is odd
    # x = a^{phi(m)-1} mod m. phi(2^k) = 2^{k-1}
    phi = m // 2
    return power_mod(a, phi - 1, m)

@njit
def count_intersections(S, d, B):
    """
    Enumerates all words of length d and shift S.
    Computes rho_w and checks if it falls in [2^{B-1}, 2^B).
    Returns total words, and number of hits.
    """
    mod = 1 << (S + 1)
    # inv3 = 3^{-d} mod 2^{S+1}
    inv3 = mod_inverse(power_mod(3, d, mod), mod)
    
    # Interval bounds for rho_w
    lower = 1 << (B - 1)
    upper = 1 << B
    
    hits = 0
    total = 0
    
    # To enumerate combinations of (d-1) elements from (S-1),
    # we can use a simple recursive generator, but numba doesn't support yield well.
    # Let's use an iterative approach (Gosper's hack or simple array).
    # Since S<=35, we can use a bitmask if S < 64!
    # A bitmask of length S-1 with exactly d-1 bits set.
    
    # Initial mask: lowest d-1 bits set
    mask = (1 << (d - 1)) - 1
    limit = 1 << (S - 1)
    
    while mask < limit:
        # Decode mask into prefix sums S_1, S_2, ..., S_{d-1}
        # and compute c_d = sum_{j=0}^{d-1} 2^{S_j} 3^{d-1-j} mod 2^{S+1}
        # S_0 = 0.
        
        c_d = power_mod(3, d - 1, mod) # j=0 term, S_0=0
        
        # We can compute c_d iteratively
        # Actually, reconstructing the positions from the mask:
        temp_mask = mask
        pos = 1
        j = 1
        while temp_mask > 0:
            if temp_mask & 1:
                # S_j = pos
                # term = 2^{pos} * 3^{d-1-j} mod mod
                term = (1 << pos) * power_mod(3, d - 1 - j, mod)
                c_d = (c_d + term) % mod
                j += 1
            temp_mask >>= 1
            pos += 1
            
        # Now we have c_d.
        # rho_w = (2^S - c_d) * 3^{-d} mod 2^{S+1}
        rho_w = (((1 << S) - c_d) % mod * inv3) % mod
        
        if lower <= rho_w < upper:
            hits += 1
        total += 1
        
        # Gosper's hack to get next mask with same number of bits
        if mask == 0:
            break
        c = mask & -mask
        r = mask + c
        if r >= limit:
            break
        mask = (((r ^ mask) >> 2) // c) | r
        
    return total, hits

def main():
    print("Experiment CIT: Measuring Transversality Factor tau(S)")
    print("Target interval I = [2^{B-1}, 2^B)")
    print("Expected hits = Total * |I| / 2^{S+1}")
    print(f"{'S':>3} | {'d':>3} | {'sigma':>5} | {'Total Words':>12} | {'Exp Hits':>10} | {'Act Hits':>10} | {'tau(S)':>10} | {'Time':>6}")
    print("-" * 80)
    
    B = 16
    # Try S from B+2 up to 30.
    # Keep sigma = S/d approx 1.7 (low shift, dense anomalies)
    sigma_target = 1.7
    
    # warmup
    count_intersections(10, 6, 8)
    
    for S in range(B + 2, 29):
        d = int(np.round(S / sigma_target))
        
        t0 = time.time()
        total, hits = count_intersections(S, d, B)
        elapsed = time.time() - t0
        
        # Expected hits: |I|_odd = 2^{B-2}. Probability = 2^{B-2} / 2^S = 2^{B-2-S}.
        exp_hits = total * (2**(B - 2 - S))
        
        tau = hits / exp_hits if exp_hits > 0 else 0.0
        
        print(f"{S:3d} | {d:3d} | {S/d:5.2f} | {total:12d} | {exp_hits:10.2f} | {hits:10d} | {tau:10.4f} | {elapsed:5.1f}s", flush=True)
        
if __name__ == "__main__":
    main()
