import numpy as np
import math
import multiprocessing
import time

def simulate_tx(args):
    measure, x, y_start, y_end, num_samples = args
    if measure == 'uniform':
        min_idx = math.ceil(y_start)
        if min_idx % 2 == 0: min_idx += 1
        max_idx = math.floor(y_end)
        if max_idx % 2 == 0: max_idx -= 1
        num_odds = (max_idx - min_idx) // 2 + 1
        indices = np.random.randint(0, num_odds, size=num_samples, dtype=np.int64)
        N_vals = min_idx + 2 * indices
    else: # logarithmic
        U = np.random.rand(num_samples)
        N_vals_float = y_start * ((y_end / y_start) ** U)
        N_vals = (np.round(N_vals_float)).astype(np.int64)
        N_vals = np.where(N_vals % 2 == 0, N_vals + 1, N_vals)
    
    T_vals = np.zeros(num_samples, dtype=np.int32)
    for i in range(num_samples):
        n = int(N_vals[i])
        steps = 0
        while n > x:
            n = 3 * n + 1
            n = n // (n & -n)
            steps += 1
        T_vals[i] = steps
        
    return T_vals

def main():
    x = 100000.0
    alpha = 1.5
    y_start = x ** alpha
    y_end = y_start ** alpha
    num_samples = 400000
    
    d = math.log(4/3)
    ln_x = math.log(x)
    m_0 = math.floor(((alpha - 1) / 100.0) * ln_x)
    
    sup_I_y = math.log(y_end / x) / d - (ln_x ** 0.8)
    
    tasks = [
        ('uniform', x, y_start, y_end, num_samples),
        ('log', x, y_start, y_end, num_samples)
    ]
    
    print(f"Running C3 Top-extended check with {num_samples} samples per measure...")
    t0 = time.time()
    with multiprocessing.Pool(2) as pool:
        results = pool.map(simulate_tx, tasks)
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
        
    T_u = results[0]
    T_l = results[1]
    
    unif_above_sup = np.mean(T_u > sup_I_y)
    log_in_I_y = np.mean((T_l >= m_0) & (T_l <= sup_I_y))
    
    med_u = np.median(T_u)
    med_l = np.median(T_l)
    
    print("\n--- C3: Top Extended Check (T_x concentration) ---")
    print(f"Parameters: x={x}, alpha={alpha}")
    print(f"Tao's I_y bounds: m_0={m_0}, sup I_y={sup_I_y:.2f}")
    print(f"Uniform mass with T_x > sup I_y: {unif_above_sup:.4f}  (Expected >= 0.9)")
    print(f"Log mass with T_x in I_y:        {log_in_I_y:.4f}  (Expected >= 0.8)")
    print(f"Median T_x (Uniform):            {med_u}")
    print(f"Median T_x (Log):                {med_l}")
    print(f"Difference (Uniform median - Log median): {med_u - med_l}")

if __name__ == '__main__':
    main()
