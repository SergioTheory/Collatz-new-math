import numpy as np
import math
import itertools
import time

def exact_restricted_sum(M, d, h, bucket_fraction=0.1, N_max=1e9):
    # Enumerate all compositions of M into d parts
    # A composition is equivalent to choosing d-1 split points from M-1 possible spots
    
    mod_exact = 1 << (M + 1)
    inv3 = pow(3, -1, mod_exact)
    inv3_d = pow(inv3, d, mod_exact)
    
    N_bucket = bucket_fraction * N_max
    
    restricted_sum = 0j
    unrestricted_sum = 0j
    total_Q = 0
    
    # We will generate combinations for the prefix sums S_1, ..., S_{d-1}
    # S_i are strictly increasing, 1 <= S_i <= M-1
    spots = list(range(1, M))
    
    count = 0
    for combo in itertools.combinations(spots, d - 1):
        # combo is S_1, S_2, ..., S_{d-1}
        S = [0] + list(combo) + [M]
        
        c_w = 0
        for i in range(1, d + 1):
            # a_i = S[i] - S[i-1]
            # c_w += 3**(d - i) * 2**(S[i-1])
            c_w += (3**(d - i)) * (1 << S[i-1])
            
        # compute rho_w
        rho_w = (( (1 << M) - c_w ) * inv3_d) % mod_exact
        
        if rho_w % 2 == 0:
            rho_w += mod_exact
            
        r_w = (rho_w - 1) // 2
        
        # compute y_w
        y_w = (3**d * rho_w + c_w) // (1 << M)
        
        # compute allowed q range
        # y_w + 2 * 3^d * q in [0, N_bucket]
        # q in [ -y_w / (2 * 3^d), (N_bucket - y_w) / (2 * 3^d) ]
        denom = 2 * (3**d)
        q_min = math.ceil(-y_w / denom)
        q_max = math.floor((N_bucket - y_w) / denom)
        
        Q_w = max(0, q_max - q_min + 1)
        
        phase = 2 * math.pi * h * r_w / (1 << (M - 1))
        val_w = np.exp(1j * phase)
        
        q_phase = 2 * math.pi * h * (3**d) / (1 << (M - 1))
        
        # exact q-sum via geometric progression
        if abs(q_phase % (2 * math.pi)) < 1e-12:
            q_sum = Q_w
        else:
            x = np.exp(1j * q_phase)
            q_sum = (np.exp(1j * q_phase * q_min) - np.exp(1j * q_phase * (q_max + 1))) / (1 - x)
            
        restricted_sum += val_w * q_sum
        
        unrestricted_sum += val_w 
        
        total_Q += Q_w
        
        count += 1
        
    return restricted_sum, unrestricted_sum, count, total_Q

def main():
    M = 24
    d = 12
    h = 1
    
    print(f"=== EXACT VALIDATION FOR M={M}, d={d} ===")
    
    t0 = time.time()
    res, unres, count, total_Q = exact_restricted_sum(M, d, h, bucket_fraction=0.1, N_max=1e15)
    t1 = time.time()
    
    print(f"Total words: {count}")
    print(f"Exact Restricted Sum:   |I| = {abs(res):.4f}")
    print(f"Exact Unrestricted Sum: |S| = {abs(unres):.4f}")
    
    log2_W_res = math.log2(total_Q) if total_Q > 0 else 0
    log2_W_unres = math.log2(count) if count > 0 else 0
    
    log2_res = math.log2(abs(res)) if abs(res) > 0 else 0
    log2_unres = math.log2(abs(unres)) if abs(unres) > 0 else 0
    
    print(f"Restricted Theta:   {log2_res / log2_W_res:.6f}")
    print(f"Unrestricted Theta: {log2_unres / log2_W_unres:.6f}")
    print(f"Time: {t1 - t0:.2f}s")

if __name__ == '__main__':
    main()
