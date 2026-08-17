#!/usr/bin/env python3
"""shadow_ldp_test.py — Empirical LDP Verification for Collatz II.
Step 1.1: Direct measurement of exceptional set (LDP shadowing) via 2-adic valuation density.
"""

import numpy as np
import random
import math
import multiprocessing
import time

K_MIN, K_MAX = 30, 45
NUM_PER_K = 100_000
D_MAX = 80
WORKERS = 30

D_EVAL = list(range(10, D_MAX + 1, 5))
SIGMAS = [1.4, 1.33, 1.2, 1.0]

def I_iid(sigma):
    """Analytic LDP rate for iid Geom(2) steps (in bits)."""
    if sigma <= 1.0: return 1.0
    two_t = sigma / (2.0 * (sigma - 1.0))
    t = math.log2(two_t)
    return -t * sigma + math.log2(2.0 * two_t - 1.0)

def simulate_chunk(args):
    k, num_samples = args
    rng = random.Random()
    
    # Store counts of successful events. Shape: (len(SIGMAS), len(D_EVAL))
    counts = np.zeros((len(SIGMAS), len(D_EVAL)), dtype=np.int32)
    
    for i in range(num_samples):
        # generate odd number in [2**(k-1), 2**k]
        x = rng.randint(2**(k-1), 2**k)
        if x % 2 == 0: x += 1
        
        s = 0
        for d_idx in range(D_MAX):
            if x == 1:
                break # trajectory collapsed, s considered infinite for remaining d
                
            # 1 odd step
            x = 3 * x + 1
            # trailing zeros
            even_steps = (x & -x).bit_length() - 1
            x >>= even_steps
            s += even_steps
            
            d_real = d_idx + 1
            if d_real in D_EVAL:
                eval_idx = D_EVAL.index(d_real)
                for sig_idx, sigma in enumerate(SIGMAS):
                    if s <= math.floor(sigma * d_real):
                        counts[sig_idx, eval_idx] += 1
                        
    return counts

def main():
    # Import scipy inside main to avoid DLL load issues in spawned workers on Windows
    from scipy import stats
    
    print(f"== Collatz II: Step 1.1 - Empirical LDP Shadowing ==")
    
    tasks = []
    # Pooling over k
    for k in range(K_MIN, K_MAX + 1):
        num_chunks = max(1, NUM_PER_K // 10000)
        chunk_size = NUM_PER_K // num_chunks
        for _ in range(num_chunks):
            tasks.append((k, chunk_size))
            
    print(f"Spawning {len(tasks)} tasks over {WORKERS} workers...")
    print(f"Total N_pool = {(K_MAX - K_MIN + 1) * NUM_PER_K:,}")
    t0 = time.time()
    
    with multiprocessing.Pool(WORKERS) as pool:
        results = pool.map(simulate_chunk, tasks)
        
    total_counts = np.sum(results, axis=0) # shape: (4, 15)
    N_pool = (K_MAX - K_MIN + 1) * NUM_PER_K
    print(f"Simulation done in {time.time()-t0:.2f}s.\n")
    
    for sig_idx, sigma in enumerate(SIGMAS):
        print(f"=== Sigma = {sigma} ===")
        if sigma == 1.0: max_d = 25
        elif sigma == 1.2: max_d = 50
        else: max_d = 80
        
        valid_indices = [i for i, d in enumerate(D_EVAL) if d <= max_d]
        if not valid_indices: continue
        
        P_vals = []
        d_vals = []
        c_vals = []
        
        for idx in valid_indices:
            count = total_counts[sig_idx, idx]
            if count >= 5:
                P_vals.append(count / N_pool)
                d_vals.append(D_EVAL[idx])
                c_vals.append(count)
                
        if len(d_vals) < 2:
            print("Not enough points to fit (requires >= 2 points with count >= 5).")
            print()
            continue
            
        log2P = np.log2(P_vals)
        d_array = np.array(d_vals)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(d_array, log2P)
        empirical_I = -slope
        
        # Bootstrap
        num_boot = 200
        boot_slopes = []
        for _ in range(num_boot):
            boot_counts = np.random.binomial(N_pool, P_vals)
            boot_P = boot_counts / N_pool
            valid_idx = boot_counts >= 5
            if np.sum(valid_idx) >= 2:
                bslope, _, _, _, _ = stats.linregress(d_array[valid_idx], np.log2(boot_P[valid_idx]))
                boot_slopes.append(-bslope)
                
        err = np.std(boot_slopes) if boot_slopes else std_err
        
        print(f"d points: {d_vals}")
        print(f"Counts  : {c_vals}")
        print(f"Empirical I(sigma): {empirical_I:.4f} +/- {err:.4f}")
        
        if sigma == 1.33:
            I_markov = 0.175
            I_iid_val = I_iid(sigma)
            print(f"Theory Markov (I) : {I_markov:.4f}")
            print(f"Theory IID (I_iid): {I_iid_val:.4f}")
            z_markov = abs(empirical_I - I_markov) / err if err > 0 else 0
            z_iid = (I_iid_val - empirical_I) / err if err > 0 else 0
            print(f"Distance to Markov: {z_markov:.1f} sigma")
            print(f"Distance to IID   : {z_iid:.1f} sigma")
            if z_markov <= 2.0 and z_iid >= 3.0:
                print("SUCCESS: Empirical matches Markov and strongly rejects IID.")
            else:
                print("WARNING: Test criteria not strictly met.")
                
        elif sigma == 1.0:
            I_markov = 0.575
            I_iid_val = 1.0
            print(f"Theory Markov (I) : {I_markov:.4f}")
            print(f"Theory IID (I_iid): {I_iid_val:.4f}")
            z_markov = abs(empirical_I - I_markov) / err if err > 0 else 0
            print(f"Distance to Markov: {z_markov:.1f} sigma")
            
        else:
            print(f"Theory IID (I_iid): {I_iid(sigma):.4f}")
            
        print()

if __name__ == "__main__":
    main()
