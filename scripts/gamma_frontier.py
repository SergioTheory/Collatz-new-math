"""
gamma_frontier.py

Diagnostic experiment G1: Find the Sampled Archimedean Lift Existence Frontier.
Investigates if there exist valuation grammars that:
1. Are 2-adically admissible and explicitly checked.
2. Have positive asymptotic drift (S/d < log2 3).
3. Have a real positive integer lift in [2^(B-1), 2^B).
4. Survive strictly above N0 = 2^(B-1).

Computes sampled_S_max(d) for different lengths d.
"""

import numpy as np
import random
from math import log2, log1p, ceil
import time

LN2 = log2(2.0)
LOG2_3 = log2(3.0)

def random_composition(S, d):
    """Generate a random composition of S into d positive integers."""
    if S < d:
        return None
    splits = random.sample(range(1, S), d - 1)
    splits.sort()
    splits = [0] + splits + [S]
    return [splits[i+1] - splits[i] for i in range(d)]

def get_affine_coefficients(word):
    d = len(word)
    S = sum(word)
    
    c = [0] * (d + 1)
    S_k = [0] * (d + 1)
    for k in range(d):
        S_k[k+1] = S_k[k] + word[k]
        c[k+1] = 3 * c[k] + (1 << S_k[k])
    
    mod = 1 << (S + 1)
    inv3d = pow(3, -d, mod)
    rho_w = (((1 << S) - c[d]) * inv3d) % mod
    if rho_w < 0:
        rho_w += mod
        
    A = [0] * (d + 1)
    B = [0] * (d + 1)
    
    A[0] = rho_w
    B[0] = 1 << (S + 1)
    
    for k in range(1, d + 1):
        num = 3**k * rho_w + c[k]
        den = 1 << S_k[k]
        
        if num % den != 0:
            return None, None, None, None, None
            
        A[k] = num // den
        B[k] = 3**k * (1 << (S + 1 - S_k[k]))
        
        if A[k] % 2 == 0:
            return None, None, None, None, None
            
        if 3 * A[k-1] + 1 != (1 << word[k-1]) * A[k]:
            return None, None, None, None, None
            
    return rho_w, A, B, c, S_k

def min_q_for_survival(A, B, N0):
    q_min = 0
    d = len(A) - 1
    for k in range(1, d + 1):
        if A[k] <= N0:
            q_k = (N0 - A[k]) // B[k] + 1
            if q_k > q_min:
                q_min = q_k
    return q_min

def evaluate_word(word, B_barrier, min_tail_len=10):
    d = len(word)
    S = sum(word)
    N0 = 1 << (B_barrier - 1)
    
    res = get_affine_coefficients(word)
    if res[0] is None:
        return {"has_lift": False}
        
    rho_w, A, B, c, S_k = res
    q_min = min_q_for_survival(A, B, N0)
    
    x0 = rho_w + (1 << (S + 1)) * q_min
    
    lower_bound = 1 << (B_barrier - 1)
    upper_bound = 1 << B_barrier
    
    q_lift = -1
    has_lift = False
    
    if x0 < lower_bound:
        q_new = (lower_bound - rho_w + (1 << (S + 1)) - 1) // (1 << (S + 1))
        if q_new > q_min:
            q_min = q_new
            x0 = rho_w + (1 << (S + 1)) * q_min
            
    if lower_bound <= x0 < upper_bound:
        has_lift = True
        q_lift = q_min
        
    sigma_eff = S / d
    Gamma_asym = LOG2_3 - sigma_eff
    
    C_d = 0.0
    Gamma_exact = 0.0
    Gamma_tail = 0.0
    
    if has_lift:
        sum_log = 0.0
        sum_log_tail = 0.0
        tail_start = d - min_tail_len + 1
        
        for k in range(1, d + 1):
            xk = A[k] + B[k] * q_lift
            correction = log1p(1.0 / (3.0 * xk)) / LN2
            sum_log += correction
            if k >= tail_start:
                sum_log_tail += correction
                
        C_d = sum_log / d
        Gamma_exact = Gamma_asym + C_d
        
        if min_tail_len <= d:
            Gamma_tail = Gamma_asym + sum_log_tail / min_tail_len
        else:
            Gamma_tail = Gamma_exact
            
    return {
        "has_lift": has_lift,
        "sigma_eff": sigma_eff,
        "Gamma_asym": Gamma_asym,
        "C_d": C_d,
        "Gamma_exact": Gamma_exact,
        "Gamma_tail": Gamma_tail
    }

def find_S_max_lift(d, B_barrier, S_window=20, max_samples=20000):
    """
    For a given d, find the maximum S (where S/d < log2 3) that has AT LEAST ONE lift.
    We scan S downwards from ceil(d * log2 3) - 1.
    """
    S_start = ceil(d * LOG2_3) - 1
    S_min = max(d, S_start - S_window)
    
    for S in range(S_start, S_min - 1, -1):
        if S < d:
            break
            
        lifts_found = 0
        best_Gamma_exact = -1.0
        best_Gamma_tail = -1.0
        
        for _ in range(max_samples):
            word = random_composition(S, d)
            if not word:
                continue
            res = evaluate_word(word, B_barrier)
            if res["has_lift"]:
                lifts_found += 1
                best_Gamma_exact = max(best_Gamma_exact, res["Gamma_exact"])
                best_Gamma_tail = max(best_Gamma_tail, res["Gamma_tail"])
                
        if lifts_found > 0:
            sigma_eff = S / d
            Gamma_asym = LOG2_3 - sigma_eff
            return S, sigma_eff, Gamma_asym, lifts_found, best_Gamma_exact, best_Gamma_tail
            
    return None, None, None, 0, None, None

def main():
    print("=" * 85)
    print("G1 DIAGNOSTIC: Sampled Archimedean Lift Existence Frontier")
    print("WARNING: This uses random sampling. 0 sampled lifts != 0 solutions.")
    print("=" * 85)
    
    B_barrier = 26
    S_window = 30
    print(f"Barrier B = {B_barrier} (N0 = 2^{B_barrier-1}), S_window = {S_window}")
    
    test_d = list(range(6, 19, 2)) + [20, 25, 30, 35, 40, 45, 50]
    
    print(f"\n{'d':>4} | {'smp_S':>5} | {'sigma_eff':>9} | {'G_asym':>8} | {'G_ex_max':>11} | {'G_tail_max':>10} | {'pos_drift_lifts':>15}")
    print("-" * 85)
    
    t0 = time.time()
    for d in test_d:
        samples = 10000 if d <= 20 else 5000
        S, sigma, G_asym, lifts, G_ex, G_tail = find_S_max_lift(d, B_barrier, S_window=S_window, max_samples=samples)
        
        if S is not None:
            print(f"{d:>4} | {S:>5} | {sigma:>9.5f} | {G_asym:>8.5f} | {G_ex:>11.5f} | {G_tail:>10.5f} | {lifts:>15}")
        else:
            print(f"{d:>4} | {'-':>5} | {'-':>9} | {'-':>8} | {'-':>11} | {'-':>10} | {'0':>15}")
            
    print("-" * 85)
    print(f"Time: {time.time() - t0:.2f}s")
    print("\nInterpretation:")
    print("If the sampled lift frontier remains uniformly below log2(3) as d grows,")
    print("this is numerical evidence of an Archimedean-2-adic gap for the sampled word ensemble.")
    print("This is NOT a proof that no divergent trajectory exists.")

if __name__ == "__main__":
    main()
