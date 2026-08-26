"""
ergodic_bridge2.py

D6: Path-Wise Time-Ergodicity Test (Birkhoff Average)
Unlike D5 which computes the ensemble average (one-step transition),
this script computes the Birkhoff time-average along a SINGLE massive deterministic trajectory.

We generate a random integer x0 of ~100,000 bits.
We run the exact Collatz dynamics until x=1 (approx 240,000 odd steps).
We track the histogram of x_k mod 2^S for S = 4, 8, 12 over time.
We compute the Total Variation (TV) distance between the empirical time-average
and the uniform Haar measure on odd classes (1 / 2^{S-1}).

If TV -> 0 as n -> inf, the deterministic Collatz trajectory is path-wise ergodic,
meaning it natively refreshes its lower bits and cannot artificially ride a Diophantine resonance.
"""

import random
import time
import sys

# Increase string-to-int conversion limit if we print
sys.set_int_max_str_digits(1000000)

def compute_tv_distance(histogram, S):
    """Compute Total Variation distance between histogram and uniform measure."""
    total = sum(histogram.values())
    if total == 0: return 1.0
    
    num_classes = 1 << (S - 1)
    uniform_prob = 1.0 / num_classes
    
    tv = 0.0
    # Iterate over all odd residues mod 2^S
    for i in range(num_classes):
        residue = 2 * i + 1
        emp_prob = histogram.get(residue, 0) / total
        tv += abs(emp_prob - uniform_prob)
        
    return tv / 2.0

def run_pathwise_ergodicity():
    bits = 100000
    print("=========================================================================")
    print(f"D6: PATH-WISE TIME-ERGODICITY ON {bits}-BIT DETERMINISTIC ORBIT")
    print("=========================================================================")
    
    # Generate random odd integer of `bits` bits
    x0 = random.getrandbits(bits) | 1 | (1 << (bits - 1))
    
    S_vals = [4, 8, 12]
    histograms = {S: {} for S in S_vals}
    
    steps = 0
    x = x0
    
    # Tracking points for output
    checkpoints = [1000, 10000, 50000, 100000, 200000]
    checkpoint_idx = 0
    
    t0 = time.time()
    
    print(f"{'Steps (n)':>10} | {'TV(S=4)':>10} | {'TV(S=8)':>10} | {'TV(S=12)':>10}")
    print("-" * 50)
    
    while x > 1:
        # Record modular classes
        for S in S_vals:
            mod = 1 << S
            res = x & (mod - 1)
            histograms[S][res] = histograms[S].get(res, 0) + 1
            
        steps += 1
        
        # Output checkpoints
        if checkpoint_idx < len(checkpoints) and steps == checkpoints[checkpoint_idx]:
            tv_4 = compute_tv_distance(histograms[4], 4)
            tv_8 = compute_tv_distance(histograms[8], 8)
            tv_12 = compute_tv_distance(histograms[12], 12)
            print(f"{steps:>10} | {tv_4:>10.5f} | {tv_8:>10.5f} | {tv_12:>10.5f}")
            checkpoint_idx += 1
            
        # Standard step
        x = 3 * x + 1
        while x % 2 == 0:
            x //= 2
            
    # Final output
    tv_4 = compute_tv_distance(histograms[4], 4)
    tv_8 = compute_tv_distance(histograms[8], 8)
    tv_12 = compute_tv_distance(histograms[12], 12)
    print(f"{steps:>10} | {tv_4:>10.5f} | {tv_8:>10.5f} | {tv_12:>10.5f} (FINAL)")
    
    print("-" * 50)
    print(f"Total time: {time.time() - t0:.2f}s")
    print("Interpretation:")
    print("If TV decays to ~0, the trajectory is path-wise ergodic. The deterministic")
    print("orbit inherently covers the 2-adic measure space evenly over time, proving")
    print("it cannot restrict its lower bits to ride Diophantine anomalies.")

if __name__ == "__main__":
    run_pathwise_ergodicity()
