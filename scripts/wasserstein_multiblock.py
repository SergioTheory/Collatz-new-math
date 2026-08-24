import numpy as np
import math
import csv
from numba import njit, prange

@njit(parallel=True)
def run_one_block(vals, d, N0):
    alive = np.ones(len(vals), dtype=np.bool_)
    new_vals = np.empty_like(vals)
    
    for i in prange(len(vals)):
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
            new_vals[i] = x
        else:
            alive[i] = False
            
    return new_vals, alive

@njit
def compute_W1(endpoints_mod, M):
    W1 = 0.0
    n_emp = len(endpoints_mod)
    if n_emp == 0:
        return 0.0
        
    for k in range(1, M + 1):
        mod_k = 1 << k
        counts_emp = np.zeros(mod_k, dtype=np.int64)
        for i in range(n_emp):
            val = endpoints_mod[i]
            counts_emp[val & (mod_k - 1)] += 1
            
        L1 = 0.0
        # uniform measure has weight n_emp / (2^{k-1}) on odd residues
        uni_weight = n_emp / (1 << (k - 1))
        
        for r in range(1, mod_k, 2):
            diff = abs(counts_emp[r] - uni_weight)
            L1 += diff
            
        L1_norm = L1 / n_emp
        W1 += (2.0 ** (-k)) * L1_norm
        
    return W1
    
@njit
def get_W1_baseline(sample_size, M):
    # simulate uniform odd residues to find finite sample noise
    endpoints = np.empty(sample_size, dtype=np.int64)
    # generate random odd numbers mod 2^M
    for i in range(sample_size):
        # np.random.randint is not fully featured in numba sometimes without bounds, 
        # but we can do it simply by generating 31-bit randoms
        r = np.random.randint(0, 1 << 30)
        endpoints[i] = (r * 2 + 1) & ((1 << M) - 1)
        
    return compute_W1(endpoints, M)

def main():
    print("2.3 Wasserstein Multiblock Contractivity")
    B_vals = [20, 22, 24, 26, 28]
    alpha = 1.05
    d = 10
    K = 15 # Only first 15 blocks to keep sample size reasonable
    M_proj = 15 # 2-adic precision to project
    
    print(f"{'B':>3} | {'Block k':>7} | {'Survivors':>10} | {'W1_act':>10} | {'W1_noise':>10} | {'rho':>8}")
    print("-" * 65)
    
    with open('wasserstein_multiblock.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['B', 'k', 'survivors', 'W1_act', 'W1_noise', 'rho'])
        
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
                vals = np.arange(L, U + 1, 2, dtype=np.int64)
            else:
                indices = np.random.choice(num_odds, sample_size, replace=False)
                vals = L + 2 * indices
                
            W1_prev = None
            
            for k in range(1, K + 1):
                new_vals, alive = run_one_block(vals, d, N0)
                vals = new_vals[alive]
                
                n_surv = len(vals)
                if n_surv < 100:
                    break
                    
                # mod reduction
                endpoints_mod = vals & ((1 << M_proj) - 1)
                W1_act = compute_W1(endpoints_mod, M_proj)
                W1_noise = get_W1_baseline(n_surv, M_proj)
                
                rho = W1_act / W1_prev if W1_prev is not None and W1_prev > 0 else 0.0
                W1_prev = W1_act
                
                print(f"{B:3d} | {k:7d} | {n_surv:10d} | {W1_act:10.5f} | {W1_noise:10.5f} | {rho:8.3f}", flush=True)
                writer.writerow([B, k, n_surv, W1_act, W1_noise, rho])

if __name__ == "__main__":
    main()
