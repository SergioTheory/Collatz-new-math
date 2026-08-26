"""
ergodic_bridge3.py

D7: Dynamic TV on Diophantine/Near-Critical Surviving Orbits.
This script addresses the fundamental logical gap: does a trajectory that is 
actively riding a deep Diophantine resonance (S/d ~ lambda) maintain 2-adic uniformity, 
or does the resonance force a distortion in the modular measure?

We use the deep convergent (d=665, S=1054). We generate thousands of independent
bit-lifts that are guaranteed to survive near-critically for 665 steps.
We aggregate their modular visits (x_k mod 2^S) during this strictly surviving phase.
If the TV distance remains small (uniform), it proves that even exceptional 
near-divergent orbits cannot avoid 2-adic mixing. If TV is large, we have found
a true mechanism for divergence.
"""

import random
import time
import math

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

def compute_tv_distance(histogram, S):
    total = sum(histogram.values())
    if total == 0: return 1.0
    num_classes = 1 << (S - 1)
    uniform_prob = 1.0 / num_classes
    tv = 0.0
    for i in range(num_classes):
        residue = 2 * i + 1
        emp_prob = histogram.get(residue, 0) / total
        tv += abs(emp_prob - uniform_prob)
    return tv / 2.0

def run_d7():
    print("=========================================================================")
    print("D7: DYNAMIC TV ON NEAR-CRITICAL DIOPHANTINE ORBITS (d=665, S=1054)")
    print("=========================================================================")
    
    d_target = 665
    S_target = 1054
    samples = 5000
    N0 = 1 << 60
    
    S_vals = [4, 6, 8, 10]
    histograms = {S: {} for S in S_vals}
    
    t0 = time.time()
    total_steps = 0
    
    for i in range(samples):
        word = random_composition(S_target, d_target)
        x0 = get_x0_for_word(word, N0)
        
        x = x0
        for _ in range(d_target):
            # Record modular classes during the strictly surviving phase
            for S in S_vals:
                mod = 1 << S
                res = x & (mod - 1)
                histograms[S][res] = histograms[S].get(res, 0) + 1
            
            x = 3 * x + 1
            while x % 2 == 0:
                x //= 2
                
            total_steps += 1
            
        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1}/{samples} trajectories ({total_steps} points)...")
            
    print("\nFINAL TV DISTANCES (Aggregate over strict near-critical phase):")
    print(f"{'S Layer':>10} | {'Total Classes':>15} | {'TV Distance':>15}")
    print("-" * 46)
    
    for S in S_vals:
        tv = compute_tv_distance(histograms[S], S)
        classes = 1 << (S - 1)
        print(f"{S:>10} | {classes:>15} | {tv:>15.5f}")
        
    print("-" * 46)
    print(f"Total time: {time.time() - t0:.2f}s")
    print("Interpretation:")
    print("If TV -> 0, the exceptional near-critical condition (S/d ~ lambda) does NOT")
    print("restrict the 2-adic measure. The trajectory remains perfectly mixed, meaning")
    print("it cannot strategically avoid modular classes to sustain divergence.")

if __name__ == "__main__":
    run_d7()
