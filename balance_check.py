import json
import os
from math import log2
from scipy.stats import linregress

def get_centers():
    algebra_path = r"C:\Users\Admin\Documents\Collatz\data\algebra_centers.json"
    centers = {}
    if os.path.exists(algebra_path):
        with open(algebra_path, 'r') as f:
            alg = json.load(f)
            if 'factorization' in alg:
                for k, v in alg['factorization'].items():
                    centers[int(k)] = int(v['center'])
    return centers

def get_forward_rate(c):
    cur = c
    d = 0
    max_val = c
    max_d = 0
    
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
            d += 1
            while cur % 2 == 0:
                cur //= 2
            if cur > max_val:
                max_val = cur
                max_d = d
        else:
            cur //= 2
            if cur % 2 != 0 and cur > max_val:
                max_val = cur
                max_d = d
                
    P = max_val.bit_length()
    bits_c = c.bit_length()
    d_peak = max_d
    
    if d_peak > 0:
        r_fwd = (P - bits_c) / d_peak
    else:
        r_fwd = 0
        
    return P, bits_c, d_peak, r_fwd

def get_preimages(x, max_val):
    preimages = []
    if x % 3 == 0:
        return preimages
    
    a = 2 if x % 3 == 1 else 1
    while True:
        y = (x * (1 << a) - 1) // 3
        if y > max_val:
            break
        if y % 2 != 0:
            preimages.append(y)
        a += 2
    return preimages

def get_backward_entropy(c, P, max_depth=15):
    max_val = (1 << P) - 1
    current_layer = [c]
    
    log_counts = []
    depths = []
    
    for k in range(1, max_depth + 1):
        next_layer = []
        for x in current_layer:
            next_layer.extend(get_preimages(x, max_val))
            
        if not next_layer:
            break
            
        current_layer = next_layer
        log_counts.append(log2(len(current_layer)))
        depths.append(k)
        
        # Prevent memory/time blowup
        if len(current_layer) > 100000:
            break
            
    if len(depths) > 1:
        slope, intercept, r, p, err = linregress(depths, log_counts)
        return slope
    elif len(depths) == 1:
        return log_counts[0]
    else:
        return 0

if __name__ == '__main__':
    centers = get_centers()
    print("Running Balance Check: Forward vs Backward Rates...")
    print(f"{'Peak':<5} | {'bits(c)':<7} | {'alpha':<7} | {'d_fwd':<6} | {'r_fwd':<8} | {'h_rev':<8} | {'Diff':<8}")
    print("-" * 65)
    
    for p in sorted(centers.keys()):
        c = centers[p]
        P, bits_c, d_fwd, r_fwd = get_forward_rate(c)
        h_rev = get_backward_entropy(c, P, max_depth=20)
        
        alpha = bits_c / P if P > 0 else 0
        diff = abs(r_fwd - h_rev)
        
        print(f"{P:<5} | {bits_c:<7} | {alpha:<7.4f} | {d_fwd:<6} | {r_fwd:<8.4f} | {h_rev:<8.4f} | {diff:<8.4f}")
