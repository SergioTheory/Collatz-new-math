import numpy as np
import math
import multiprocessing
import time

def simulate_pass_x(args):
    measure, x, y_start, y_end, num_samples = args
    # Sample initial values
    if measure == 'uniform':
        min_idx = math.ceil(y_start)
        if min_idx % 2 == 0: min_idx += 1
        max_idx = math.floor(y_end)
        if max_idx % 2 == 0: max_idx -= 1
        num_odds = (max_idx - min_idx) // 2 + 1
        
        # Max integer is ~10^16.8, well within 64-bit int bounds for numpy
        indices = np.random.randint(0, num_odds, size=num_samples, dtype=np.int64)
        N_vals = min_idx + 2 * indices
    else: # logarithmic
        U = np.random.rand(num_samples)
        # We need N distributed as 1/N. For large interval, exponential of uniform.
        N_vals_float = y_start * ((y_end / y_start) ** U)
        N_vals = (np.round(N_vals_float)).astype(np.int64)
        N_vals = np.where(N_vals % 2 == 0, N_vals + 1, N_vals)
    
    # Compute Pass_x
    passes = np.zeros(num_samples, dtype=np.int32)
    for i in range(num_samples):
        n = int(N_vals[i]) # Use Python int to prevent any overflow on 3*n+1
        while n > x:
            n = 3 * n + 1
            # fast trailing zeros
            n = n // (n & -n)
        passes[i] = n % 81
        
    return passes

def main():
    x = 100000.0
    alpha = 1.5
    y1_start = x ** alpha
    y1_end = y1_start ** alpha
    
    y2_start = x ** (alpha**2)
    y2_end = y2_start ** alpha
    
    num_samples = 400000
    
    tasks = [
        ('uniform', x, y1_start, y1_end, num_samples),
        ('uniform', x, y2_start, y2_end, num_samples),
        ('log', x, y1_start, y1_end, num_samples),
        ('log', x, y2_start, y2_end, num_samples)
    ]
    
    print(f"Running C2 D-check with {num_samples} samples per scale...")
    t0 = time.time()
    with multiprocessing.Pool(4) as pool:
        results = pool.map(simulate_pass_x, tasks)
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
        
    def get_dist(passes):
        counts = np.bincount(passes, minlength=81)
        # only odd residues modulo 81 are reachable for odd N passing x
        return counts / np.sum(counts)
        
    p_u1 = get_dist(results[0])
    p_u2 = get_dist(results[1])
    p_l1 = get_dist(results[2])
    p_l2 = get_dist(results[3])
    
    tv_u = 0.5 * np.sum(np.abs(p_u1 - p_u2))
    tv_l = 0.5 * np.sum(np.abs(p_l1 - p_l2))
    tv_cross1 = 0.5 * np.sum(np.abs(p_u1 - p_l1))
    
    print("--- C2: Allikvere D check (Pass_x mod 81) ---")
    print(f"TV(Uniform y1, Uniform y2): {tv_u:.4f}  (Expected <= 0.01)")
    print(f"TV(Log y1, Log y2):         {tv_l:.4f}  (Expected <= 0.01)")
    print(f"TV(Uniform y1, Log y1):     {tv_cross1:.4f}  (Expected <= 0.01)")

if __name__ == '__main__':
    main()
