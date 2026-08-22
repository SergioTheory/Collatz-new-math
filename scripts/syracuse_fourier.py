import numpy as np
import math
import cmath

def compute_distributions(max_n):
    # P_n as an array of length 3^n
    P = np.array([1.0])
    
    dists = [P]
    
    for n in range(max_n):
        mod_curr = 3**n
        mod_next = 3**(n+1)
        
        P_next = np.zeros(mod_next)
        denom = 1.0 - 2.0**(-2 * mod_curr)
        
        for a in range(1, 2 * mod_curr + 1):
            req_rem = 1 if a % 2 == 0 else 2
            
            valid_xs = np.arange(req_rem, mod_next, 3)
            
            # use python int for big pow
            pow2a = int(pow(2, a, mod_next))
            
            # (2^a * x - 1) / 3 mod 3^n
            vals = [((pow2a * x - 1) // 3) % mod_curr for x in valid_xs]
            
            P_next[valid_xs] += (2.0**(-a)) * P[vals]
            
        P_next /= denom
        P = P_next
        dists.append(P_next)
        
        # compute fourier
        xi = 1
        xs = np.arange(mod_next)
        angles = -2 * math.pi * xi * xs / mod_next
        expected_val = np.sum(P_next * np.exp(1j * angles))
        decay = abs(expected_val)
        
        print(f"n={n+1}: Fourier |E e^{{-2 pi i x / 3^{n+1}}}| = {decay:.6e} (approx 2^{math.log2(decay):.3f})", flush=True)
        
    return dists

if __name__ == '__main__':
    compute_distributions(10)
