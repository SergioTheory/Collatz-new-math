import time
import math
from numba import njit
import numpy as np

@njit
def power(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return res

@njit
def modInverse(a, m):
    m0 = m
    y = 0
    x = 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        t = m
        m = a % m
        a = t
        t = y
        y = x - q * y
        x = t
    if x < 0:
        x += m0
    return x

@njit
def run_dfs(M, B, Q, bucket_start, mu):
    mod_B = 1 << B
    mod_M1 = 1 << (M + 1)
    
    stack_d = np.zeros(M * M + 100, dtype=np.int64)
    stack_S = np.zeros(M * M + 100, dtype=np.int64)
    stack_cw = np.zeros(M * M + 100, dtype=np.int64)
    
    sp = 0
    stack_d[sp] = 0
    stack_S[sp] = 0
    stack_cw[sp] = 0
    sp += 1
    
    sum_eps = 0.0
    sum_abs_eps = 0.0
    W_count = 0
    
    while sp > 0:
        sp -= 1
        d = stack_d[sp]
        S = stack_S[sp]
        c_w = stack_cw[sp]
        
        if S == M:
            W_count += 1
            p3_d = power(3, d, mod_M1)
            inv3 = modInverse(p3_d, mod_M1)
            
            diff = (1 << M) - c_w
            diff = diff % mod_M1
            if diff < 0: diff += mod_M1
            
            N_0 = (diff * inv3) % mod_M1
            
            y_0 = (power(3, d, mod_M1) * N_0 + c_w) >> M
            
            step = (2 * power(3, d, mod_B)) % mod_B
            y_q = y_0 % mod_B
            if y_q < 0: y_q += mod_B
            
            hits = 0
            for _ in range(Q):
                if y_q >= bucket_start:
                    hits += 1
                y_q = (y_q + step) % mod_B
                
            eps = hits - Q * mu
            sum_eps += eps
            sum_abs_eps += abs(eps)
            continue
            
        for a in range(M - S, 0, -1):
            stack_d[sp] = d + 1
            stack_S[sp] = S + a
            stack_cw[sp] = 3 * c_w + (1 << S)
            sp += 1
            
    return sum_eps, sum_abs_eps, W_count

def run_e10():
    B = 16
    Q = 10
    bucket_start = int(0.9 * (1 << B))
    if bucket_start % 2 == 0:
        bucket_start += 1
        
    odds_in_bucket = ((1 << B) - bucket_start + 1) // 2
    mu = odds_in_bucket / (1 << (B - 1))
    
    print(f"=== E10 Aggregate Cancellation Lemma Test ===")
    print(f"B = {B}, Q = {Q}, bucket_start = {bucket_start} (mu = {mu:.4f})")
    print("Testing if |Sum eps| scales as sqrt(W) rather than W\n")

    for M in [22, 24, 26, 28]:
        t0 = time.time()
        # Numba compilation on first call (M=16) will take a bit, but fast after
        sum_eps, sum_abs_eps, W = run_dfs(M, B, Q, bucket_start, mu)
        
        print(f"M={M:2d} | W={W:9d} | Time: {time.time()-t0:5.2f}s")
        print(f"   Sum |eps| (Naive W bound): {sum_abs_eps:.2f}")
        print(f"   |Sum eps| (Actual error):  {abs(sum_eps):.2f}")
        
        if sum_abs_eps > 0:
            ratio_W = abs(sum_eps) / sum_abs_eps
            ratio_sqrt = abs(sum_eps) / math.sqrt(sum_abs_eps)
            print(f"   Ratio to W:      {ratio_W:.6f}")
            print(f"   Ratio to sqrt:   {ratio_sqrt:.6f}\n")

if __name__ == "__main__":
    run_e10()
