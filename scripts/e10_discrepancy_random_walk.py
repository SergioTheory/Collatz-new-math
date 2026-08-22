import time
import math

def dfs_discrepancy(M, B, Q, bucket_start):
    odds_in_bucket = ((1 << B) - bucket_start + 1) // 2
    mu = odds_in_bucket / (1 << (B - 1))
    
    stack = [(0, 0, 0)]
    sum_eps = 0.0
    sum_abs_eps = 0.0
    W = 0
    
    mod_B = 1 << B
    mod_M1 = 1 << (M + 1)
    
    while stack:
        d, S, c_w = stack.pop()
        
        if S == M:
            W += 1
            inv3 = pow(3, -d, mod_M1)
            N_0 = (((1 << M) - c_w) * inv3) % mod_M1
            
            y_0 = (pow(3, d) * N_0 + c_w) >> M
            
            hits = 0
            step = (2 * pow(3, d)) % mod_B
            y_q = y_0 % mod_B
            
            for _ in range(Q):
                if y_q >= bucket_start:
                    hits += 1
                y_q = (y_q + step) % mod_B
                
            eps = hits - Q * mu
            sum_eps += eps
            sum_abs_eps += abs(eps)
            continue
            
        for a in range(1, M - S + 1):
            stack.append((d + 1, S + a, 3 * c_w + (1 << S)))
            
    return sum_eps, sum_abs_eps, W

def run_e10():
    B = 16
    Q = 10
    bucket_start = int(0.9 * (1 << B))
    if bucket_start % 2 == 0:
        bucket_start += 1
        
    print(f"=== E10 Aggregate Cancellation Lemma Test ===", flush=True)
    print(f"Testing if |Sum eps| scales as sqrt(W) rather than W\n", flush=True)

    for M in [14, 16, 18, 20, 22]:
        t0 = time.time()
        sum_eps, sum_abs_eps, W = dfs_discrepancy(M, B, Q, bucket_start)
        
        print(f"M={M:2d} | W={W:9d} | Time: {time.time()-t0:5.2f}s", flush=True)
        print(f"   Sum |eps| (Naive W bound): {sum_abs_eps:.2f}", flush=True)
        print(f"   |Sum eps| (Actual error):  {abs(sum_eps):.2f}", flush=True)
        
        if sum_abs_eps > 0:
            ratio_W = abs(sum_eps) / sum_abs_eps
            ratio_sqrt = abs(sum_eps) / math.sqrt(sum_abs_eps)
            print(f"   Ratio to W:      {ratio_W:.6f}", flush=True)
            print(f"   Ratio to sqrt:   {ratio_sqrt:.6f}\n", flush=True)

if __name__ == "__main__":
    run_e10()
