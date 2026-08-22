import numpy as np
import math
from numba import njit
import itertools
import time

@njit
def naive_spectrum(M, d, h_list):
    K = 1 << M
    sums = np.zeros(len(h_list), dtype=np.complex128)
    
    for z in range(K):
        N = 2 * z + 1
        curr = N
        S = 0
        
        for step in range(1, d + 1):
            curr = 3 * curr + 1
            a = 0
            while curr % 2 == 0:
                a += 1
                curr //= 2
            S += a
                
        if S <= M:
            # print("NAIVE ADD: z=", z, "S=", S)
            for i in range(len(h_list)):
                h = h_list[i]
                sums[i] += np.exp(-2j * np.pi * h * z / K)
                
    for i in range(len(h_list)):
        sums[i] /= K
        
    return sums

def exact_spectrum(M, d, h_list):
    results = np.zeros(len(h_list), dtype=np.complex128)
    
    for i, h in enumerate(h_list):
        if h == 0:
            v = M
        else:
            v = 0
            temp = h
            while temp % 2 == 0 and temp > 0:
                v += 1
                temp //= 2
                
        S_min = max(d, M - v)
        if S_min > M:
            continue
            
        sum_h = 0j
        
        for S in range(S_min, M + 1):
            mod_exact = 1 << (S + 1)
            inv3_d = pow(3, -d, mod_exact)
            
            spots = list(range(1, S))
            for combo in itertools.combinations(spots, d - 1):
                S_arr = [0] + list(combo) + [S]
                
                c_w = 0
                for j in range(1, d + 1):
                    c_w += (3**(d - j)) * (1 << S_arr[j-1])
                    
                rho_w = (( (1 << S) - c_w ) * inv3_d) % mod_exact
                if rho_w % 2 == 0:
                    rho_w += mod_exact
                    
                r_w = (rho_w - 1) // 2
                
                phase = -2 * math.pi * h * r_w / (1 << M)
                term = (2.0 ** -S) * np.exp(1j * phase)
                sum_h += term
                # if h == 1:
                #     print("THEORY ADD: S=", S, "r_w=", r_w, "term=", term)
                
        results[i] = sum_h
        
    return results

def main():
    M = 22
    d = 11
    h_list = [1, 2, 3, 4, 15]
    
    print(f"Spot-checking boundary-layer spectrum for M={M}, d={d}")
    print(f"Frequencies: {h_list}")
    
    t0 = time.time()
    naive_res = naive_spectrum(M, d, np.array(h_list, dtype=np.int64))
    t1 = time.time()
    print(f"Naive evaluation took {t1 - t0:.2f}s")
    
    t0 = time.time()
    exact_res = exact_spectrum(M, d, h_list)
    t1 = time.time()
    print(f"Theoretical evaluation took {t1 - t0:.2f}s")
    
    print("-" * 50)
    for i, h in enumerate(h_list):
        n_val = naive_res[i]
        e_val = exact_res[i]
        err = abs(n_val - e_val)
        print(f"h = {h:2d} | Naive: {n_val.real:10.7f} + {n_val.imag:10.7f}j | Theory: {e_val.real:10.7f} + {e_val.imag:10.7f}j | Error: {err:.2e}")
        
    if np.allclose(naive_res, exact_res, atol=1e-10):
        print("SUCCESS: Theoretical formula matches naive evaluation up to machine precision.")
    else:
        print("FAILURE: Mismatch detected!")

if __name__ == '__main__':
    main()
