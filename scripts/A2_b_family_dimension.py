import numpy as np
import math
import multiprocessing

def compute_offsets(args):
    b, n, num_samples = args
    A = np.random.geometric(p=0.5, size=(num_samples, n))
    
    offsets = np.zeros(num_samples, dtype=np.int64)
    modulus = int(b ** n)
    b_pows = [int(pow(b, n - 1 - j, modulus)) for j in range(n)]
    
    for i in range(num_samples):
        F = 0
        S = 0
        for j in range(n):
            term = (b_pows[j] * pow(2, int(S), modulus)) % modulus
            F = (F + term) % modulus
            S += A[i, j]
        offsets[i] = F
        
    return offsets

def main():
    b_vals = [3, 5, 7]
    n_vals = [6, 8, 10]
    
    num_samples_per_core = 500000
    cores = 4
    total_samples = num_samples_per_core * cores
    
    print("--- A2: Family Dimension Test (Empirical) ---")
    print(f"Total samples per test: {total_samples}")
    
    for b in b_vals:
        print(f"\nTesting b = {b}")
        expected_D2 = math.log(3) / math.log(b)
        expected_D1 = math.log(4) / math.log(b)
        
        print(f"Expected D_2 (Collision): {expected_D2:.3f}")
        print(f"Expected D_1 (Shannon):   {expected_D1:.3f}")
        
        for n in n_vals:
            tasks = [(b, n, num_samples_per_core) for _ in range(cores)]
            with multiprocessing.Pool(cores) as pool:
                results = pool.map(compute_offsets, tasks)
                
            all_offsets = np.concatenate(results)
            
            _, counts = np.unique(all_offsets, return_counts=True)
            counts = counts.astype(np.float64)
            C_n_est = np.sum(counts * (counts - 1)) / (total_samples * (total_samples - 1))
            
            if C_n_est > 0:
                D2_est = -math.log(C_n_est) / (n * math.log(b))
            else:
                D2_est = float('nan')
                
            p = counts / total_samples
            num_nonzero = len(p)
            H_n_est = -np.sum(p * np.log(p)) + (num_nonzero - 1) / (2 * total_samples) # Bias correction
            D1_est = H_n_est / (n * math.log(b))
            
            print(f"  n={n:2d}: D_2_est = {D2_est:.3f}, D_1_est = {D1_est:.3f} (Unique offsets: {num_nonzero})")

if __name__ == '__main__':
    main()
