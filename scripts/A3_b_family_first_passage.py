import numpy as np
import math
import multiprocessing
import time

def simulate_pass_x(args):
    measure, b, x, y_start, y_end, num_samples = args
    if measure == 'uniform':
        min_idx = math.ceil(y_start)
        if min_idx % 2 == 0: min_idx += 1
        max_idx = math.floor(y_end)
        if max_idx % 2 == 0: max_idx -= 1
        num_odds = (max_idx - min_idx) // 2 + 1
        indices = np.random.randint(0, num_odds, size=num_samples, dtype=np.int64)
        N_vals = min_idx + 2 * indices
    
    passes = []
    
    for i in range(num_samples):
        n = int(N_vals[i])
        steps = 0
        while n > x:
            n = b * n + 1
            n = n // (n & -n)
            steps += 1
            if n > 1e16 or steps > 5000:
                n = -1 
                break
        if n != -1:
            passes.append(n % (b**4))
            
    return passes

def main():
    b = 5
    x = 100000.0
    alpha = 1.5
    y1_start = x ** alpha
    y1_end = y1_start ** alpha
    y2_start = x ** (alpha**2)
    y2_end = y2_start ** alpha
    
    num_samples = 2000000 # Large sample count to detect rare large deviations
    
    tasks = [
        ('uniform', b, x, y1_start, y1_end, num_samples),
        ('uniform', b, x, y2_start, y2_end, num_samples)
    ]
    
    print(f"Running A3 First Passage test for b={b} with {num_samples} samples per scale...")
    t0 = time.time()
    with multiprocessing.Pool(2) as pool:
        results = pool.map(simulate_pass_x, tasks)
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
    
    passes_u1 = results[0]
    passes_u2 = results[1]
    
    defect_u1 = len(passes_u1) / num_samples
    defect_u2 = len(passes_u2) / num_samples
    
    print(f"\n--- A3: Family First Passage (b={b}) ---")
    print(f"Defect P(T_x < inf) at y1={y1_start:.2e}: {defect_u1:.6e}")
    print(f"Defect P(T_x < inf) at y2={y2_start:.2e}: {defect_u2:.6e}")
    
    if len(passes_u1) > 0 and len(passes_u2) > 0:
        def get_dist(passes):
            counts = np.bincount(passes, minlength=b**4)
            return counts / np.sum(counts)
            
        p_u1 = get_dist(passes_u1)
        p_u2 = get_dist(passes_u2)
        
        tv_u = 0.5 * np.sum(np.abs(p_u1 - p_u2))
        print(f"TV(Uniform y1, Uniform y2 | T_x < inf): {tv_u:.4f}  (Expected: stabilization absent or limit differs)")
    else:
        print("Not enough samples with T_x < inf to compute TV.")

if __name__ == '__main__':
    main()
