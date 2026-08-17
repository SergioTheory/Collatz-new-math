import json
import os
from math import log2

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

def compute_defect_gas(c):
    # Trace the canonical path from c to its peak
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
    
    # Correct formula: delta_defect = d_peak * (log2(3) - 4/3) - (P - bits_c)
    G_act = P - bits_c
    delta_defect = d_peak * (log2(3) - (4/3)) - G_act
    
    return d_peak, bits_c, G_act, delta_defect

if __name__ == '__main__':
    centers = get_centers()
    print("Running Phase 5 Instanton Statistics (Corrected Base Line)...")
    print(f"{'Peak':<5} | {'Center':<25} | {'d_peak':<7} | {'bits(c)':<7} | {'G_act':<10} | {'Delta_def':<10}")
    print("-" * 80)
    for p in sorted(centers.keys()):
        c = centers[p]
        d_peak, bits_c, G_act, delta_defect = compute_defect_gas(c)
        print(f"{p:<5} | {c:<25} | {d_peak:<7} | {bits_c:<7} | {G_act:<10.4f} | {delta_defect:<10.4f}")
