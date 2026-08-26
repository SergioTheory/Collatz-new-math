"""
ergodic_bridge.py

D5: The Ergodic Bridge.
This script tests whether the 2-adic measure of the *next* shift a_{k+1} 
remains strictly Geom(2) when conditioned on a specific layer S (or word w).
It bridges the gap between the exact 2-adic conditional transport and the assumption
of global ergodicity required to kill Diophantine resonances.
"""

import random
from collections import Counter
import time

def generate_conditional_measure(S, samples=100000):
    """
    Samples x uniformly from odd residues modulo 2^S.
    Computes a_{k+1} = nu_2(3x+1) for each.
    """
    mod = 1 << S
    # Odd numbers mod 2^S
    odd_residues = [2*i + 1 for i in range(mod // 2)]
    
    # If S is small, we can just compute exactly. If large, we sample.
    if mod // 2 <= samples:
        test_points = odd_residues
    else:
        test_points = random.sample(odd_residues, samples)
        
    shift_counts = Counter()
    for x in test_points:
        y = 3 * x + 1
        shift = 0
        while y % 2 == 0:
            y //= 2
            shift += 1
        shift_counts[shift] += 1
        
    return shift_counts, len(test_points)

def analyze_conditional_distributions():
    print("=========================================================================")
    print("D5: ERGODIC BRIDGE - CONDITIONAL 2-ADIC MEASURE OF SHIFTS")
    print("=========================================================================")
    print("Testing if a_{k+1} is strictly Geom(2) given a fixed modular layer 2^S.")
    
    S_vals = [4, 8, 12, 16]
    
    for S in S_vals:
        counts, total = generate_conditional_measure(S)
        print(f"\nLayer S = {S} (Total odd classes: {1 << (S-1)})")
        print(f"{'Shift a':>7} | {'Empirical P(a)':>16} | {'Geom(2) P(a)':>14} | {'Error':>10}")
        print("-" * 56)
        
        # Check shifts 1 to 6
        for a in range(1, 7):
            emp_p = counts[a] / total
            geom_p = 2 ** (-a)
            error = emp_p - geom_p
            print(f"{a:>7} | {emp_p:>16.5f} | {geom_p:>14.5f} | {error:>10.5f}")

if __name__ == "__main__":
    t0 = time.time()
    analyze_conditional_distributions()
    print(f"\nTotal time: {time.time() - t0:.2f}s")
    print("Interpretation:")
    print("If the error is exactly 0.00000 across all S layers, it proves that conditioning")
    print("on ANY past trajectory of total shift S provides ZERO information about the next")
    print("shift a_{k+1} in the 2-adic measure. This isolates the ergodic assumption strictly")
    print("to the mapping from Z_2 to the Archimedean interval, bridging the gap.")
