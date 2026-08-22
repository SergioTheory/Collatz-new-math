import numpy as np
import itertools
import math

def debug_mismatch():
    M = 10
    d = 5
    K = 1 << M
    h = 1
    
    # Naive sums by word
    naive_by_word = {}
    for z in range(K):
        N = 2 * z + 1
        curr = N
        S = 0
        word = []
        for step in range(1, d + 1):
            curr = 3 * curr + 1
            a = 0
            while curr % 2 == 0:
                a += 1
                curr //= 2
            word.append(a)
            S += a
        
        if S <= M:
            w = tuple(word)
            phase = -2 * np.pi * h * z / K
            naive_by_word[w] = naive_by_word.get(w, 0j) + np.exp(1j * phase) / K
            
    # Theory sums by word
    theory_by_word = {}
    v = 0
    S_min = max(d, M - v)
    for S in range(S_min, M + 1):
        mod_exact = 1 << (S + 1)
        inv3_d = pow(3, -d, mod_exact)
        spots = list(range(1, S))
        for combo in itertools.combinations(spots, d - 1):
            S_arr = [0] + list(combo) + [S]
            word = []
            c_w = 0
            for j in range(1, d + 1):
                word.append(S_arr[j] - S_arr[j-1])
                c_w += (3**(d - j)) * (1 << S_arr[j-1])
            w = tuple(word)
            
            rho_w = (( (1 << S) - c_w ) * inv3_d) % mod_exact
            if rho_w % 2 == 0:
                rho_w += mod_exact
            r_w = (rho_w - 1) // 2
            
            phase = -2 * math.pi * h * r_w / K
            term = (2.0 ** -S) * np.exp(1j * phase)
            theory_by_word[w] = term
            
    sum_n = sum(naive_by_word.values())
    sum_t = sum(theory_by_word.values())
    print(f"Total Naive Sum: {sum_n}")
    print(f"Total Theory Sum: {sum_t}")

debug_mismatch()
