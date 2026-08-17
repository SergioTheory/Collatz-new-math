import json
import random
import multiprocessing
import os
from collections import defaultdict
import math

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

def collatz_to_peak(n):
    cur = n
    d = 0
    S = 0
    max_val = n
    max_d = 0
    max_S = 0
    path = {n}
    
    while cur > 1:
        if cur % 2 != 0:
            cur = cur * 3 + 1
            d += 1
            while cur % 2 == 0:
                cur //= 2
                S += 1
            path.add(cur)
            if cur > max_val:
                max_val = cur
                max_d = d
                max_S = S
        else:
            cur //= 2
            S += 1
            if cur % 2 != 0:
                path.add(cur)
                if cur > max_val:
                    max_val = cur
                    max_d = d
                    max_S = S
                
    return max_val.bit_length(), max_d, max_S, path

def worker(args):
    start_seed, num_samples, centers = args
    random.seed(start_seed)
    
    results = {}
    
    for _ in range(num_samples):
        # sample random odd number from 10 to 60 bits
        bits = random.randint(10, 60)
        n = random.getrandbits(bits)
        if n % 2 == 0:
            n += 1
            
        peak, max_d, max_S, path = collatz_to_peak(n)
        
        # Must reach a peak higher than the start, so max_d > 0
        if 14 <= peak <= 51 and peak in centers and max_d > 0:
            c = centers[peak]
            sd = max_S / max_d
            
            if peak not in results:
                results[peak] = {'soliton_sd': [], 'center_sd': []}
                
            if c in path:
                results[peak]['center_sd'].append(sd)
            else:
                results[peak]['soliton_sd'].append(sd)
                
    return results

if __name__ == '__main__':
    centers = get_centers()
    num_workers = 16
    samples_per_worker = 10000
    
    pool = multiprocessing.Pool(num_workers)
    args = [(i, samples_per_worker, centers) for i in range(num_workers)]
    
    print("Running Phase 4 Soliton Census...")
    results = pool.map(worker, args)
    
    merged = defaultdict(lambda: {'soliton_sd': [], 'center_sd': []})
    for r in results:
        for p, data in r.items():
            merged[p]['soliton_sd'].extend(data['soliton_sd'])
            merged[p]['center_sd'].extend(data['center_sd'])
            
    # Report
    print(f"{'Peak':<5} | {'Solitons':<10} | {'Centers':<10} | {'Soliton %':<10} | {'Mean SD Sol':<12} | {'Mean SD Cen':<12}")
    print("-" * 70)
    for p in sorted(merged.keys()):
        sol_list = merged[p]['soliton_sd']
        cen_list = merged[p]['center_sd']
        num_sol = len(sol_list)
        num_cen = len(cen_list)
        total = num_sol + num_cen
        if total == 0: continue
        
        sol_pct = num_sol / total * 100
        mean_sd_sol = sum(sol_list)/num_sol if num_sol > 0 else 0
        mean_sd_cen = sum(cen_list)/num_cen if num_cen > 0 else 0
        
        print(f"{p:<5} | {num_sol:<10} | {num_cen:<10} | {sol_pct:<10.2f}% | {mean_sd_sol:<12.4f} | {mean_sd_cen:<12.4f}")
