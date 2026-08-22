import numpy as np
import time
from numba import njit
import sys

@njit
def compute_inner_sum(M_head, tail_array, M, h=1):
    # tail_array is an array of shifts for the tail.
    # M_head is the weight of the head. M = M_head + sum(tail_array).
    d_tail = len(tail_array)
    
    # Precompute powers of 3 modulo 2^{M+1}
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
        
    # We enumerate all heads of weight M_head.
    stack_d = np.zeros(M_head * M_head + 100, dtype=np.int32)
    stack_S = np.zeros(M_head * M_head + 100, dtype=np.int32)
    stack_cw = np.zeros(M_head * M_head + 100, dtype=np.int64)
    
    sp = 0
    stack_d[sp] = 0
    stack_S[sp] = 0
    stack_cw[sp] = 0
    sp += 1
    
    total_sum = 0j
    W = 0
    
    while sp > 0:
        sp -= 1
        d_head = stack_d[sp]
        S_head = stack_S[sp]
        cw_head = stack_cw[sp]
        
        if S_head == M_head:
            W += 1
            
            # Now append the tail
            c_w = cw_head
            S = S_head
            d = d_head
            
            for i in range(d_tail):
                c_w = (3 * c_w + (1 << S)) % mod_exact
                S += tail_array[i]
                d += 1
                
            # c_w is now the full c_w, d is the full length, S should be M.
            inv3 = inv3_arr[d]
            rho_w = ((1 << M) - c_w) % mod_exact
            if rho_w < 0: rho_w += mod_exact
            rho_w = (rho_w * inv3) % mod_exact
            r_w = (rho_w - 1) // 2
            
            phase = 2 * np.pi * h * r_w / (1 << M)
            total_sum += np.exp(1j * phase)
            
            continue
            
        for a in range(M_head - S_head, 0, -1):
            stack_d[sp] = d_head + 1
            stack_S[sp] = S_head + a
            stack_cw[sp] = (3 * cw_head + (1 << S_head)) % mod_exact
            sp += 1
            
    return W, total_sum

def main():
    # Fix M_head to 20, which has 2^19 = 524,288 compositions. Fast to sum.
    M_head = 20
    print(f"=== Inner Sum over Heads (M_head = {M_head}) ===")
    
    tails_to_test = [
        [1, 1, 1, 1],
        [2, 2],
        [4],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [4, 4],
        [8]
    ]
    
    # Just compiling numba
    compute_inner_sum(4, np.array([1, 1]), 6, 1)
    
    for tail in tails_to_test:
        tail_arr = np.array(tail, dtype=np.int32)
        tail_weight = np.sum(tail_arr)
        M = M_head + tail_weight
        
        t0 = time.time()
        W, sum_val = compute_inner_sum(M_head, tail_arr, M, h=1)
        t1 = time.time()
        
        mag = abs(sum_val)
        sqrt_W = np.sqrt(W)
        ratio = mag / sqrt_W
        
        # alpha = 0.5 - log(mag / sqrt_W) / log(W)
        # where mag = W^alpha.
        # Wait, mag = W^theta -> theta = log(mag) / log(W)
        theta = np.log(mag) / np.log(W)
        
        print(f"Tail {tail} (weight {tail_weight}, full M={M}):")
        print(f"  W_head = {W}, |I_head| = {mag:.2f}")
        print(f"  |I_head| / sqrt(W) = {ratio:.4f}")
        print(f"  Implied exponent theta = {theta:.4f} (random walk = 0.5)")
        print(f"  Time: {t1-t0:.2f}s\n")

if __name__ == '__main__':
    main()
