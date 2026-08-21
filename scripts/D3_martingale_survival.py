import numpy as np
import math
import time
from numba import njit, prange

@njit
def solve_dp_exact(d, B):
    max_S = int(d * math.log2(3.0) + B) + 10
    dp = np.zeros(max_S, dtype=np.float64)
    dp[0] = 1.0
    
    log3 = math.log2(3.0)
    
    for k in range(1, d + 1):
        next_dp = np.zeros(max_S, dtype=np.float64)
        limit = int(k * log3 + B)
        
        # S can range from k to limit
        for S in range(k, limit + 1):
            term1 = dp[S - 1] * 0.5
            term2 = next_dp[S - 1] * 0.5
            next_dp[S] = term1 + term2
            
        dp = next_dp
        
    return np.sum(dp)

@njit(parallel=True)
def run_mc_survival(d, B, num_trials):
    survived = 0
    log3 = math.log2(3.0)
    for _ in prange(num_trials):
        S = 0.0
        alive = True
        for k in range(1, d + 1):
            # simulate geom(2) via uniform
            u = np.random.random()
            # a = floor(-log2(1-u)) + 1
            # actually numba doesn't support np.random.geometric in all versions, 
            # let's just do it manually for speed and compatibility
            a = 1
            while True:
                u *= 2.0
                if u > 1.0:
                    break
                a += 1
            
            S += log3 - a
            if S < -B:
                alive = False
                break
        if alive:
            survived += 1
    return survived / num_trials

def run_martingale():
    print("--- D3: Martingale Survival & Exact Combinatorics ---")
    
    B_vals = [5, 10, 15]
    d_vals = [100, 500, 1000, 5000]
    num_trials = 10000000  # 10 million for low variance
    
    print(f"{'B':<4} | {'d':<5} | {'DP Survival':<15} | {'MC Survival':<15} | {'C * 2^{-B} (Lundberg)':<20}")
    print("-" * 75)
    
    # We calibrate the Lundberg constant C empirically from B=15, d=5000
    # Actually, we can just print the value scaled by 2^B to see the constant
    for B in B_vals:
        for d in d_vals:
            t0 = time.time()
            prob_dp = solve_dp_exact(d, B)
            t1 = time.time()
            
            # only run MC for d <= 1000 to save time, or run parallel
            if d <= 1000:
                prob_mc = run_mc_survival(d, B, num_trials)
            else:
                prob_mc = -1.0
                
            C_est = prob_dp * (2.0 ** B)
            
            mc_str = f"{prob_mc:.6e}" if prob_mc >= 0 else "N/A"
            print(f"{B:<4} | {d:<5} | {prob_dp:<15.6e} | {mc_str:<15} | C = {C_est:.4f}")

if __name__ == '__main__':
    run_martingale()
