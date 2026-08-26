"""
experiments_d2_d3.py

D2: Structure of Long-Surviving Orbits
Find orbits that survive exceptionally long above B=40, 50. 
Analyze their shift vectors to see if they possess a hidden grammatical structure,
or if they are just statistically typical sequences that got lucky.

D3: Zone-2 Capture / Cascade Test
Test how often real orbits fall into the (2, 1, 1) Zone-2 vacuum state.
The reverse map is R(x) = (16x - 29) / 27, meaning the forward sequence is (2, 1, 1).
If orbits exhibit chained (2, 1, 1) sequences significantly more than random chance (1/16),
it proves Zone-2 acts as a true dynamical attractor (capture mechanism).
"""

import time
import random
from collections import Counter
import numpy as np

def simulate_and_get_shifts(x0, N0):
    x = x0
    shifts = []
    steps = 0
    
    while x >= N0:
        if x % 2 == 0:
            shift = 0
            while x % 2 == 0:
                x //= 2
                shift += 1
            # We don't record the pure even shifts at the start, only after an odd step
            # Wait, Collatz standard odd step: x -> (3x+1)/2^a
        else:
            x = 3 * x + 1
            shift = 0
            while x % 2 == 0:
                x //= 2
                shift += 1
            shifts.append(shift)
            steps += 1
            
    return steps, shifts

def run_d2():
    print("=========================================================================")
    print("EXPERIMENT D2: STRUCTURE OF LONG-SURVIVING ORBITS")
    print("=========================================================================")
    
    B_vals = [40, 50]
    samples = 50000
    top_k = 50 # Top 0.1% survivors
    
    for B in B_vals:
        N0 = 1 << B
        results = []
        
        for _ in range(samples):
            # Pick a random odd x0 in [N0, 2*N0)
            x0 = random.randrange(N0 + 1, 2 * N0, 2)
            steps, shifts = simulate_and_get_shifts(x0, N0)
            results.append((steps, shifts))
            
        results.sort(key=lambda x: x[0], reverse=True)
        top_survivors = results[:top_k]
        
        avg_lifetime = sum(r[0] for r in results) / samples
        top_avg_lifetime = sum(r[0] for r in top_survivors) / top_k
        
        # Analyze shift distribution of top survivors
        all_top_shifts = []
        for _, shifts in top_survivors:
            all_top_shifts.extend(shifts)
            
        avg_a = sum(all_top_shifts) / len(all_top_shifts) if all_top_shifts else 0
        rho_3_plus = sum(1 for a in all_top_shifts if a >= 3) / len(all_top_shifts) if all_top_shifts else 0
        
        # Standard values for random walk: E[a] = 2, P(a>=3) = 1/4 = 0.25
        print(f"Barrier 2^{B}:")
        print(f"  Average lifetime: {avg_lifetime:.1f} steps")
        print(f"  Top {top_k} avg lifetime: {top_avg_lifetime:.1f} steps")
        print(f"  Top survivors E[a]: {avg_a:.4f} (Expected: 2.0)")
        print(f"  Top survivors P(a>=3): {rho_3_plus:.4f} (Expected: 0.25)")
        print()

def run_d3():
    print("=========================================================================")
    print("EXPERIMENT D3: ZONE-2 CAPTURE (2,1,1) CASCADE TEST")
    print("=========================================================================")
    
    N0 = 1 << 40
    samples = 10000
    
    total_triplets = 0
    total_211 = 0
    
    chain_lengths = Counter()
    
    for _ in range(samples):
        x0 = random.randrange(N0 + 1, 2 * N0, 2)
        # Run for 200 odd steps
        x = x0
        shifts = []
        for _ in range(200):
            x = 3 * x + 1
            shift = 0
            while x % 2 == 0:
                x //= 2
                shift += 1
            shifts.append(shift)
            
        # Count (2, 1, 1) occurrences
        i = 0
        current_chain = 0
        while i < len(shifts) - 2:
            total_triplets += 1
            if shifts[i] == 2 and shifts[i+1] == 1 and shifts[i+2] == 1:
                total_211 += 1
                current_chain += 1
                i += 3 # skip the triplet
            else:
                if current_chain > 0:
                    chain_lengths[current_chain] += 1
                    current_chain = 0
                i += 1
                
        if current_chain > 0:
            chain_lengths[current_chain] += 1
            
    p_empirical = total_211 / total_triplets if total_triplets > 0 else 0
    p_expected = (1/4) * (1/2) * (1/2) # 1/16 = 0.0625
    
    print(f"Total triplets analyzed: {total_triplets}")
    print(f"Occurrences of (2,1,1): {total_211}")
    print(f"Empirical probability: {p_empirical:.5f}")
    print(f"Expected independent prob: {p_expected:.5f}")
    
    print("\nChain lengths of consecutive (2,1,1):")
    for length, count in sorted(chain_lengths.items()):
        print(f"  Chain of {length}: {count} times")
        
    print("\nInterpretation:")
    print("If empirical probability perfectly matches expected (0.0625) and long chains are rare,")
    print("then Zone-2 is not an attractor for random points. If probability is elevated and chains")
    print("are remarkably long, the confluence (capture mechanism) is proven.")

if __name__ == "__main__":
    t0 = time.time()
    run_d2()
    run_d3()
    print(f"Total time: {time.time() - t0:.2f}s")
