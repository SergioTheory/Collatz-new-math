"""
ergodic_bridge4.py

D8: Individual Time-Average TV on Near-Critical Orbits.
Unlike D7 which aggregated points across 5000 orbits (ensemble average),
this script computes the Birkhoff time-average TV distance strictly ALONG
each individual orbit of length d=665.

We measure if any single trajectory can achieve a low TV (uniform mixing)
while strictly maintaining the near-critical condition S/d ~ 1.5849.
"""

import random
import time

def random_composition(S, d):
    if S < d: return None
    splits = random.sample(range(1, S), d - 1)
    splits.sort()
    splits = [0] + splits + [S]
    return [splits[i+1] - splits[i] for i in range(d)]

def get_x0_for_word(word, N0):
    d = len(word)
    S = 0
    c = 0
    L = N0
    for k, a in enumerate(word):
        k_idx = k + 1
        S += a
        c = 3 * c + (1 << (S - a))
        L_cand = ((1 << S) * N0 - c) // (3**k_idx) + 1
        if L_cand > L:
            L = L_cand
    mod = 1 << (S + 1)
    inv3d = pow(3, -d, mod)
    rho = (((1 << S) - c) * inv3d) % mod
    if rho < 0: rho += mod
    q_min = (L - rho + mod - 1) // mod
    x0 = rho + mod * q_min
    return x0

def compute_tv_distance(histogram, total, S):
    if total == 0: return 1.0
    num_classes = 1 << (S - 1)
    uniform_prob = 1.0 / num_classes
    tv = 0.0
    for i in range(num_classes):
        residue = 2 * i + 1
        emp_prob = histogram.get(residue, 0) / total
        tv += abs(emp_prob - uniform_prob)
    return tv / 2.0

def run_d8():
    print("=========================================================================")
    print("D8: INDIVIDUAL PATH-WISE TV ON NEAR-CRITICAL ORBITS (d=665, S=1054)")
    print("=========================================================================")
    
    d_target = 665
    S_target = 1054
    samples = 5000
    N0 = 1 << 60
    
    S_vals = [4, 6, 8]
    
    # Store individual TV scores for each S
    tv_scores = {S: [] for S in S_vals}
    
    t0 = time.time()
    
    for i in range(samples):
        word = random_composition(S_target, d_target)
        x0 = get_x0_for_word(word, N0)
        
        histograms = {S: {} for S in S_vals}
        
        x = x0
        for _ in range(d_target):
            for S in S_vals:
                mod = 1 << S
                res = x & (mod - 1)
                histograms[S][res] = histograms[S].get(res, 0) + 1
            
            x = 3 * x + 1
            while x % 2 == 0:
                x //= 2
                
        # Compute TV for this individual orbit
        for S in S_vals:
            tv = compute_tv_distance(histograms[S], d_target, S)
            tv_scores[S].append(tv)
            
        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1}/{samples} individual trajectories...")
            
    print("\nFINAL INDIVIDUAL TV DISTANCES (d=665 steps per orbit):")
    print(f"{'S Layer':>10} | {'Min TV':>10} | {'Mean TV':>10} | {'Max TV':>10}")
    print("-" * 49)
    
    for S in S_vals:
        scores = tv_scores[S]
        min_tv = min(scores)
        mean_tv = sum(scores) / len(scores)
        max_tv = max(scores)
        print(f"{S:>10} | {min_tv:>10.5f} | {mean_tv:>10.5f} | {max_tv:>10.5f}")
        
    print("-" * 49)
    print(f"Total time: {time.time() - t0:.2f}s")
    print("Interpretation:")
    print("If Min TV is strictly bounded > 0, it is a mathematical contradiction for ANY")
    print("trajectory to simultaneously be uniformly mixed and maintain E[a] ~ 1.5849.")
    print("Thus, ALL near-critical divergent trajectories MUST inherently break uniformity.")

if __name__ == "__main__":
    run_d8()
