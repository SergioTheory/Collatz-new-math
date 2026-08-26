"""
near_critical_audit.py

Task A: Fill the gap for sigma in [1.30, 1.50] and test the Zone-2 core.
Validates the theoretical formula: Max Lifetime ~ d + (lambda - sigma)*d / 0.415.
"""

import time
import random
from math import log2

LOG2_3 = log2(3.0)
F1_DRAG = 0.415 # lambda - E[a] = log2(3) - 2 for typical word, wait. E[a] = 2. log2(3) = 1.58496. 1.58496 - 2 = -0.415. So drag is 0.415 bits/step.

def random_composition(S, d):
    """Generate a random composition of S into d positive integers."""
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

def simulate_orbit(x0, max_steps):
    x = x0
    steps = 0
    max_x = x0
    
    while steps < max_steps:
        if x % 2 == 0:
            x //= 2
        else:
            x = 3 * x + 1
            x //= 2
            steps += 1
            if x > max_x: max_x = x
            
            if x < x0:
                return steps, max_x, False
                
    return steps, max_x, True

def run_audit():
    sigmas = [1.30, 1.35, 1.40, 1.45, 1.50]
    ds = [100, 200, 300]
    samples_per_config = 30
    
    max_steps_sim = 10**6
    N0 = 1 << 60
    
    print("=============================================================================")
    print("TASK A: SIGMA GAP AUDIT & ZONE-2 CORE TEST")
    print("Validating formula: Max Lifetime ~ d + (log2(3) - sigma) * d / 0.415")
    print("=============================================================================")
    print(f"{'d':>4} | {'sigma':>6} | {'S':>4} | {'Max Lifetime':>12} | {'Predicted':>10} | {'Type':>10}")
    print("-" * 77)
    
    t0 = time.time()
    
    # Run the standard random grid
    for d in ds:
        for target_sigma in sigmas:
            S = int(d * target_sigma)
            if S < d: continue
            
            lifetimes = []
            for _ in range(samples_per_config):
                word = random_composition(S, d)
                x0 = get_x0_for_word(word, N0)
                steps, _, _ = simulate_orbit(x0, max_steps_sim)
                lifetimes.append(steps)
                
            max_lt = max(lifetimes)
            predicted = int(d + (LOG2_3 - target_sigma) * d / F1_DRAG)
            print(f"{d:>4} | {target_sigma:>6.3f} | {S:>4} | {max_lt:>12} | {predicted:>10} | {'Random':>10}")
            
    # Run the Zone-2 Core tests
    print("-" * 77)
    for d in ds:
        # Zone-2 core is repeating (1, 1, 2)
        word_z2 = ([1, 1, 2] * (d // 3 + 1))[:d]
        S_z2 = sum(word_z2)
        actual_sigma = S_z2 / d
        
        x0_z2 = get_x0_for_word(word_z2, N0)
        steps_z2, _, _ = simulate_orbit(x0_z2, max_steps_sim)
        
        predicted_z2 = int(d + (LOG2_3 - actual_sigma) * d / F1_DRAG)
        print(f"{d:>4} | {actual_sigma:>6.3f} | {S_z2:>4} | {steps_z2:>12} | {predicted_z2:>10} | {'Zone2-Core':>10}")

    print("-" * 77)
    print(f"Time taken: {time.time() - t0:.2f}s")
    print("Interpretation:")
    print("If the Zone-2 Core vastly outperforms the predicted F1 decay rate, it means rigid")
    print("grammars are exceptionally resilient. If it matches the prediction, then even")
    print("the most structured local core eventually decays at the universal F1 rate.")

if __name__ == "__main__":
    run_audit()
