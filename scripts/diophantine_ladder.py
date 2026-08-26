"""
diophantine_ladder.py

Directly probes the Diophantine regime (Vector B) where S/d approaches log2(3) from below.
1. Computes the continued fraction convergents of log2(3).
2. For each convergent (d, S) up to S ~ 1000, generates real bit-lift orbits.
3. Measures their lifetimes to see if the deep Diophantine gap provides anomalous survival.
4. Computes theta(d) where |d * log2(3) - S| = d^(-theta).
"""

import time
import random
import math
from decimal import Decimal, getcontext

getcontext().prec = 100
LOG2_3_DEC = Decimal(3).ln() / Decimal(2).ln()
LOG2_3 = float(LOG2_3_DEC)
F1_DRAG = 0.415

def get_convergents(max_S=1000):
    """Generate continued fraction convergents of log2(3) up to max_S."""
    x = LOG2_3_DEC
    a = []
    
    h_prev2, h_prev1 = 0, 1
    k_prev2, k_prev1 = 1, 0
    
    convergents = []
    
    for _ in range(20):
        ai = int(x)
        a.append(ai)
        
        h = ai * h_prev1 + h_prev2
        k = ai * k_prev1 + k_prev2
        
        if h > max_S:
            break
            
        # We want S/d, so S is h, d is k
        S, d = h, k
        if d > 0 and S > 0:
            convergents.append((S, d))
            
        if x - ai == 0:
            break
        x = Decimal(1) / (x - ai)
        
        h_prev2, h_prev1 = h_prev1, h
        k_prev2, k_prev1 = k_prev1, k
        
    return convergents

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
                return steps
    return steps

def main():
    print("=========================================================================================")
    print("DIOPHANTINE LADDER AUDIT (Vector B)")
    print("Testing the deepest rationally accessible gaps |S - d*log2(3)| ~ 0")
    print("=========================================================================================")
    
    convergents = get_convergents(max_S=5000)
    
    # We only care about convergents where S/d < log2(3) to have positive drift
    pos_drift_convs = [(S, d) for S, d in convergents if S/d < LOG2_3]
    
    print(f"{'d':>5} | {'S':>5} | {'sigma':>9} | {'delta':>11} | {'theta':>6} | {'Max Life':>9} | {'Predicted':>9}")
    print("-" * 89)
    
    N0 = 1 << 60
    max_steps_sim = 10**6
    samples = 30
    
    for S, d in pos_drift_convs:
        if d < 10:
            continue
            
        # delta = |S - d * lambda|
        delta = abs(S - d * LOG2_3)
        # d^(-theta) = delta => -theta * ln(d) = ln(delta) => theta = -ln(delta)/ln(d)
        theta = -math.log(delta) / math.log(d)
        
        lifetimes = []
        for _ in range(samples):
            word = random_composition(S, d)
            x0 = get_x0_for_word(word, N0)
            lt = simulate_orbit(x0, max_steps_sim)
            lifetimes.append(lt)
            
        max_lt = max(lifetimes)
        sigma = S / d
        predicted = int(d + (LOG2_3 - sigma) * d / F1_DRAG)
        
        print(f"{d:>5} | {S:>5} | {sigma:>9.6f} | {delta:>11.2e} | {theta:>6.3f} | {max_lt:>9} | {predicted:>9}")
        
    print("-" * 89)
    print("\nREFERENCE STRUCTURES (Zone-2 core, etc.):")
    print(f"{'d':>5} | {'S':>5} | {'sigma':>9} | {'delta':>11} | {'theta':>6} | {'Max Life':>9} | {'Predicted':>9}")
    print("-" * 89)
    
    # Zone-2 core d=250
    d_z2 = 250
    word_z2 = ([1, 1, 2] * (d_z2 // 3 + 1))[:d_z2]
    S_z2 = sum(word_z2)
    x0_z2 = get_x0_for_word(word_z2, N0)
    lt_z2 = simulate_orbit(x0_z2, max_steps_sim)
    delta_z2 = abs(S_z2 - d_z2 * LOG2_3)
    theta_z2 = -math.log(delta_z2) / math.log(d_z2) if delta_z2 > 0 else 0
    sigma_z2 = S_z2 / d_z2
    pred_z2 = int(d_z2 + (LOG2_3 - sigma_z2) * d_z2 / F1_DRAG)
    print(f"{d_z2:>5} | {S_z2:>5} | {sigma_z2:>9.6f} | {delta_z2:>11.2e} | {theta_z2:>6.3f} | {lt_z2:>9} | {pred_z2:>9} (Zone-2)")
    
    print("-" * 89)
    print("Interpretation:")
    print("If theta ~ 1, Diophantine gap scales as O(1/d).")
    print("If Max Life dramatically exceeds the F1 Prediction in this deep regime,")
    print("the Diophantine resonance provides hidden stability. Otherwise, F1 drag is absolute.")

if __name__ == "__main__":
    main()
