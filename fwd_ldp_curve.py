import random
import math
import numpy as np
from scipy.stats import linregress
import time

def theoretical_i2(m):
    if m <= 1.0:
        return float('inf') if m < 1.0 else 1.0
    return m + (m-1)*math.log2(m-1) - m*math.log2(m)

def get_shifts(x, max_d):
    shifts = []
    for _ in range(max_d):
        if x <= 1:
            break
        x = 3 * x + 1
        s = 0
        while x % 2 == 0:
            x //= 2
            s += 1
        shifts.append(s)
    return shifts

def main():
    ks = [100, 150, 200]
    N_per_k = 170000  # ~500k total
    sigmas = [1.0, 1.1, 1.2, 1.25, 1.3, 1.33, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2]
    
    counts = {sig: {} for sig in sigmas}
    totals = {}
    
    start_time = time.time()
    
    for k in ks:
        d_max = int(k / 2.5)
        print(f"Generating for k={k}, d_max={d_max}, N={N_per_k}")
        for _ in range(N_per_k):
            x = (random.getrandbits(k - 2) << 1) | (1 << (k - 1)) | 1
            shifts = get_shifts(x, d_max)
            
            cum_shift = 0
            for d in range(1, len(shifts) + 1):
                cum_shift += shifts[d-1]
                if d >= 20:
                    mean_shift = cum_shift / d
                    totals[d] = totals.get(d, 0) + 1
                    
                    for sig in sigmas:
                        if sig <= 2.0:
                            if mean_shift <= sig:
                                counts[sig][d] = counts[sig].get(d, 0) + 1
                        else:
                            if mean_shift >= sig:
                                counts[sig][d] = counts[sig].get(d, 0) + 1

    print(f"\nSimulation done in {time.time() - start_time:.2f} seconds.")
    print("\nExtracting I_fwd(sigma)...")
    print(f"{'Sigma':<10} | {'I_fwd':<10} | {'I_2(theory)':<15} | {'Delta':<10}")
    print("-" * 55)
    
    for sig in sigmas:
        i2 = theoretical_i2(sig) if sig > 1.0 else 1.0
        
        X = []
        Y = []
        for d in sorted(totals.keys()):
            tot = totals[d]
            c = counts[sig].get(d, 0)
            if c > 0:
                p = c / tot
                X.append(d)
                Y.append(-math.log2(p))
                
        if len(X) > 5:
            slope, intercept, r_value, p_value, std_err = linregress(X, Y)
            i_fwd = slope
        else:
            i_fwd = float('nan')
            
        delta = abs(i_fwd - i2) if not math.isnan(i_fwd) else float('nan')
        print(f"{sig:<10.2f} | {i_fwd:<10.4f} | {i2:<15.4f} | {delta:<10.4f}")

if __name__ == '__main__':
    main()
