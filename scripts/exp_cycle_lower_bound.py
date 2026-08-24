"""
Experiment: Cycle Lower Bound vs Baker's Bound
Analytically computes R(d) = W / M, and exhaustively searches for cycles 
up to d=20 to find the actual minimum N, illustrating the structural 
exclusion mechanism for Collatz cycles.
"""
import math
import time
import numpy as np
from numba import njit

@njit
def find_min_N(d, S):
    """
    Exhaustively searches all words of length d and shift S to find
    if M = 2^S - 3^d divides c_d. Returns the minimum integer N.
    """
    M = (1 << S) - 3**d
    if M <= 0:
        return -1
        
    mask = (1 << (d - 1)) - 1
    limit = 1 << (S - 1)
    min_N = -1
    
    # Precompute powers of 3 mod M
    pow3_mod = np.zeros(d, dtype=np.int64)
    pow3_exact = np.zeros(d, dtype=np.int64)
    pow3_mod[0] = 1
    pow3_exact[0] = 1
    for i in range(1, d):
        pow3_mod[i] = (pow3_mod[i-1] * 3) % M
        pow3_exact[i] = pow3_exact[i-1] * 3
        
    while mask < limit:
        c_d_mod = pow3_mod[d-1] 
        temp = mask
        pos = 1
        j = 1
        while temp > 0:
            if temp & 1:
                term = ((1 << pos) % M * pow3_mod[d - 1 - j]) % M
                c_d_mod += term
                j += 1
            temp >>= 1
            pos += 1
            
        if c_d_mod % M == 0:
            # We found a cycle! Compute exact N.
            actual_c_d = pow3_exact[d-1]
            temp = mask
            pos = 1
            j = 1
            while temp > 0:
                if temp & 1:
                    actual_c_d += (1 << pos) * pow3_exact[d - 1 - j]
                    j += 1
                temp >>= 1
                pos += 1
            
            N = actual_c_d // M
            if min_N == -1 or N < min_N:
                min_N = N
                
        if mask == 0:
            break
        c = mask & -mask
        r = mask + c
        if r >= limit:
            break
        mask = (((r ^ mask) >> 2) // c) | r
        
    return min_N

def choose(n, k):
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def main():
    print("Experiment: Structural Deficit for Collatz Cycles")
    print("R(d) = W / M, where W = choose(S-1, d-1) and M = 2^S - 3^d.")
    print("S is uniquely determined as floor(d * log2(3)) + 1.")
    print()
    
    L23 = math.log2(3.0)
    
    print(f"{'d':>3} | {'S':>3} | {'W (words)':>15} | {'M (modulus)':>15} | {'R(d) = W/M':>12} | {'Min N (search)':>15}")
    print("-" * 75)
    
    # Warmup numba
    find_min_N(2, 4)
    
    for d in range(1, 41):
        S = math.floor(d * L23) + 1
        
        M = (1 << S) - 3**d
        W = choose(S - 1, d - 1)
        
        R = W / M if M > 0 else float('inf')
        
        # Exhaustive search for d <= 22
        min_N_str = "-"
        if d <= 20:
            t0 = time.time()
            min_N = find_min_N(d, S)
            elapsed = time.time() - t0
            
            if min_N == -1:
                min_N_str = "None"
            else:
                # If d > 1 and min_N is just 1 (meaning it's the trivial cycle traversing multiple times)
                # we note it.
                if min_N == 1 and d > 1:
                    min_N_str = "1 (trivial)"
                else:
                    min_N_str = str(min_N)
                    
        print(f"{d:3d} | {S:3d} | {W:15d} | {M:15d} | {R:12.2e} | {min_N_str:>15}", flush=True)

if __name__ == "__main__":
    main()
