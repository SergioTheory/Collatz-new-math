import numpy as np
import math
import csv
from numba import njit, prange

@njit(parallel=True)
def run_blocks(starts, d, K, N0):
    alive = np.ones(len(starts), dtype=np.bool_)
    counts = np.zeros(K, dtype=np.int64)
    vals = starts.copy()
    
    for k in range(K):
        for i in prange(len(vals)):
            if not alive[i]:
                continue
            x = vals[i]
            ok = True
            for _ in range(d):
                x = 3 * x + 1
                while (x & 1) == 0:
                    x >>= 1
                if x <= N0:
                    ok = False
                    break
            if ok:
                vals[i] = x
            else:
                alive[i] = False
                
        counts[k] = np.sum(alive)
        if counts[k] == 0:
            break
            
    return counts

def fit_decay(A):
    # A_k = c_*^k * k^{-gamma}
    # log A_k = k * log(c_*) - gamma * log(k)
    # We use only geometric regime, avoiding the floor.
    # Floor is usually 10^-5 to 10^-7. Let's use A > 1e-4 and at least 3 points.
    
    valid_k = np.where(A > 1e-4)[0]
    if len(valid_k) < 3:
        valid_k = np.where(A > 0)[0]
        if len(valid_k) < 3:
            return 0.0, 0.0
            
    # skip the very first block if we have enough points, since it can have boundary artifacts
    start_idx = 1 if len(valid_k) > 4 else 0
    k_vals = valid_k[start_idx:] + 1 # k is 1-indexed
    y = np.log(A[valid_k[start_idx:]])
    
    # fit y = k * c + gamma * (-log(k))
    X = np.vstack([k_vals, -np.log(k_vals)]).T
    res, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    c_star = np.exp(res[0])
    gamma = res[1]
    return c_star, gamma

def main():
    print("2.2 Timeout Renewal Closure")
    B_vals = [20, 22, 24, 26, 28]
    alphas = [1.05, 1.10]
    d = 10
    K = 60
    
    print(f"{'B':>3} | {'alpha':>5} | {'Starts':>10} | {'c_*':>10} | {'gamma':>10} | {'rho_last':>10}")
    print("-" * 65)
    
    with open('timeout_renewal.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['B', 'alpha', 'starts', 'c_star', 'gamma', 'rho_last'])
        
        for alpha in alphas:
            for B in B_vals:
                N0 = 1 << B
                N_end = int(math.ceil(2 ** (B * alpha)))
                
                L = N0
                if L % 2 == 0: L += 1
                U = N_end
                if U % 2 == 0: U -= 1
                
                num_odds = (U - L) // 2 + 1
                sample_size = min(num_odds, 5_000_000)
                
                if sample_size == num_odds:
                    starts = np.arange(L, U + 1, 2, dtype=np.int64)
                else:
                    indices = np.random.choice(num_odds, sample_size, replace=False)
                    starts = L + 2 * indices
                    
                counts = run_blocks(starts, d, K, N0)
                A = counts / len(starts)
                
                c_star, gamma = fit_decay(A)
                
                # compute rho = A[k+1]/A[k] in the geometric regime
                valid = np.where(A > 1e-4)[0]
                if len(valid) > 1:
                    last_k = valid[-1]
                    prev_k = valid[-2]
                    if A[prev_k] > 0:
                        rho_last = A[last_k] / A[prev_k]
                    else:
                        rho_last = 0.0
                else:
                    rho_last = 0.0
                    
                print(f"{B:3d} | {alpha:5.2f} | {len(starts):10d} | {c_star:10.5f} | {gamma:10.5f} | {rho_last:10.5f}", flush=True)
                writer.writerow([B, alpha, len(starts), c_star, gamma, rho_last])

if __name__ == "__main__":
    main()
