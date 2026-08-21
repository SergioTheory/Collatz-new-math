import numpy as np
import multiprocessing
import math

def simulate_descent(args):
    b, min_idx, max_idx, N_0, d, num_samples = args
    
    num_odds = (max_idx - min_idx) // 2 + 1
    indices = np.random.randint(0, num_odds, size=num_samples, dtype=np.int64)
    N_vals = min_idx + 2 * indices
    
    survived = 0
    for i in range(num_samples):
        n = int(N_vals[i])
        ok = True
        for _ in range(d):
            if n <= N_0:
                ok = False
                break
            n = b * n + 1
            n = n // (n & -n)
        if ok:
            survived += 1
            
    return survived

def I_2(sigma):
    if sigma >= 2.0:
        return 0.0
    return sigma - sigma * math.log2(sigma) + (sigma - 1) * math.log2(sigma - 1)

def main():
    b_vals = [3, 5, 7, 9]
    Y = 2**40
    alpha = 1.10
    Y_alpha = int(Y ** alpha)
    
    N_0_vals = [2**10, 2**12, 2**14]
    t = 0.4
    
    num_samples_per_core = 500000
    cores = 4
    total_samples = num_samples_per_core * cores
    
    min_idx = Y
    if min_idx % 2 == 0: min_idx += 1
    max_idx = Y_alpha
    if max_idx % 2 == 0: max_idx -= 1
    
    print("--- A1: Family Descent Test ---")
    print(f"Y = 2^40, alpha = {alpha}, Y_alpha = 2^{40*alpha:.1f}")
    print(f"Total samples per test = {total_samples}")
    print(f"Fixed t = {t}")
    
    for b in b_vals:
        print(f"\nTesting b = {b}")
        sigma = math.log2(b) + (alpha - 1) / t
        print(f"sigma = log2({b}) + {(alpha-1):.2f}/{t} = {sigma:.4f}")
        
        for N_0 in N_0_vals:
            d = int(math.floor(t * math.log2(N_0)))
            
            tasks = [(b, min_idx, max_idx, N_0, d, num_samples_per_core) for _ in range(cores)]
            with multiprocessing.Pool(cores) as pool:
                results = pool.map(simulate_descent, tasks)
                
            survived = sum(results)
            fraction = survived / total_samples
            
            print(f"  N_0 = 2^{int(math.log2(N_0)):02d}, d = {d:2d}: Fraction survived = {fraction:.6f}", end="")
            if b == 3:
                bound = N_0 ** (-t * I_2(sigma))
                print(f"  (Bound: {bound:.6f})")
            else:
                print("  (Bound: vacuum, alpha > delta)")

if __name__ == '__main__':
    main()
