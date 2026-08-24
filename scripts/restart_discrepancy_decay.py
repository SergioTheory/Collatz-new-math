import numpy as np
import math
from numba import njit, prange
import csv
from scipy.optimize import curve_fit

@njit
def collatz_block_survival(N, d, N0):
    for _ in range(d):
        N = 3 * N + 1
        while (N & 1) == 0:
            N >>= 1
        if N <= N0:
            return -1 # dropped
    return N

@njit(parallel=True)
def run_first_block(N_start, N_end, d, N0):
    # Count odds
    if N_start % 2 == 0:
        N_start += 1
    
    num_odds = (N_end - N_start + 1) // 2
    endpoints = np.zeros(num_odds, dtype=np.int64)
    
    for i in prange(num_odds):
        N = N_start + 2 * i
        endpoints[i] = collatz_block_survival(N, d, N0)
        
    # filter out -1
    return endpoints

@njit
def count_survivors(arr, d, N0):
    count = 0
    for i in range(len(arr)):
        if collatz_block_survival(arr[i], d, N0) > 0:
            count += 1
    return count

def run_experiment(B, alpha, d=10, K=15):
    N0 = 1 << B
    N_end = int(math.ceil(2 ** (B * alpha)))
    
    # Ensure N_start is odd
    N_start = N0
    if N_start % 2 == 0:
        N_start += 1
        
    endpoints = run_first_block(N_start, N_end, d, N0)
    survivors = endpoints[endpoints > 0]
    
    if len(survivors) == 0:
        return 0, 0, 0
        
    min_E = N0
    max_E = np.max(survivors)
    
    # K log-buckets
    log_min = math.log(min_E)
    log_max = math.log(max_E)
    
    # boundaries
    boundaries = np.exp(np.linspace(log_min, log_max, K + 1))
    boundaries[-1] = max_E + 1 # inclusive upper bound
    
    delta_abs = 0.0
    delta_signed = 0.0
    
    total_survivors = len(survivors)
    
    for i in range(K):
        L_b = boundaries[i]
        U_b = boundaries[i+1]
        
        # transported points in this bucket
        mask = (survivors >= L_b) & (survivors < U_b)
        T_b = survivors[mask]
        
        if len(T_b) == 0:
            continue
            
        weight = len(T_b) / total_survivors
        
        # transported survival rate
        # we run 2nd block on T_b
        surv_trans = count_survivors(T_b, d, N0)
        S_trans = surv_trans / len(T_b)
        
        # fresh start survival rate
        # sample uniformly from odd numbers in [L_b, U_b)
        L_odd = int(math.ceil(L_b))
        if L_odd % 2 == 0:
            L_odd += 1
        U_odd = int(math.floor(U_b))
        if U_odd % 2 == 0:
            U_odd -= 1
            
        if L_odd > U_odd:
            S_fresh = 0.0
        else:
            # For exact comparability and to reduce variance, sample a large number of fresh odds
            # Or if the interval is small, just enumerate all of them
            num_fresh_odds = (U_odd - L_odd) // 2 + 1
            sample_size = min(num_fresh_odds, 50000)
            
            if sample_size == num_fresh_odds:
                fresh_sample = np.arange(L_odd, U_odd + 1, 2, dtype=np.int64)
            else:
                fresh_indices = np.random.choice(num_fresh_odds, sample_size, replace=True)
                fresh_sample = L_odd + 2 * fresh_indices
                
            surv_fresh = count_survivors(fresh_sample, d, N0)
            S_fresh = surv_fresh / len(fresh_sample)
            
        diff = S_trans - S_fresh
        delta_abs += weight * abs(diff)
        delta_signed += weight * diff
        
    return delta_abs, delta_signed, len(survivors)

def main():
    print("2.1 Restart Discrepancy Decay")
    B_vals = [16, 18, 20, 22] # added 22 for better fit
    alphas = [1.05, 1.10, 1.20]
    
    results = {alpha: [] for alpha in alphas}
    
    print(f"{'B':>3} | {'alpha':>5} | {'Survivors':>10} | {'Delta_abs':>12} | {'Delta_sgn':>12} | {'|sgn/abs|':>9}")
    print("-" * 65)
    
    with open('restart_decay.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['B', 'alpha', 'survivors', 'delta_abs', 'delta_sgn', 'ratio'])
        
        for alpha in alphas:
            for B in B_vals:
                d_abs, d_sgn, surv_count = run_experiment(B, alpha)
                ratio = abs(d_sgn) / d_abs if d_abs > 0 else 0
                
                print(f"{B:3d} | {alpha:5.2f} | {surv_count:10d} | {d_abs:12.6f} | {d_sgn:12.6f} | {ratio:9.4f}", flush=True)
                writer.writerow([B, alpha, surv_count, d_abs, d_sgn, ratio])
                
                results[alpha].append((B, d_abs, d_sgn))
                
    # Fit decay 2^{-B/2} * B^{-p}
    print("\nDecay fits:")
    def model(B, C, p):
        return C * (2.0 ** (-B / 2.0)) * (B ** (-p))
        
    for alpha in alphas:
        Bs = np.array([x[0] for x in results[alpha]])
        abs_deltas = np.array([x[1] for x in results[alpha]])
        
        if len(Bs) >= 2:
            try:
                # Log fit: log(Delta * 2^{B/2}) = log(C) - p * log(B)
                # y = log(Delta) + (B/2)*log(2)
                y = np.log(abs_deltas) + (Bs / 2.0) * np.log(2.0)
                x = np.log(Bs)
                
                # linear fit y = c - p * x
                A = np.vstack([np.ones(len(x)), -x]).T
                c, p = np.linalg.lstsq(A, y, rcond=None)[0]
                
                # Compute signed ratio avg
                sgns = np.array([abs(x[2]) for x in results[alpha]])
                avg_ratio = np.mean(sgns / abs_deltas)
                print(f"alpha={alpha:.2f} -> fit p = {p:6.3f} (C={np.exp(c):.4f}), avg |sgn/abs| = {avg_ratio:6.4f}")
            except Exception as e:
                print(f"alpha={alpha:.2f} -> fit failed: {e}")

if __name__ == "__main__":
    main()
