"""
survival_grammar_beam.py

G2: Necessary Grammar for Long Survival.
Uses beam search on valuation prefixes to find structural constraints
of arbitrarily long Archimedean survival, separating CRT scarcity
from dynamic obstruction by scaling the window B = ceil(d_max * log2(3)) + Delta.

State: (k, S_k, c_k, q_min, q_max, D_k, G_k)
Objectives for beam search (kept separate):
1. Maximize positive gain G_k
2. Maximize defect density D_k / k
3. Minimize survival pressure q_min
"""

import numpy as np
from math import log2, ceil
import time

LOG2_3 = log2(3.0)

def mod_inverse(a, m):
    return pow(a, -1, m)

def run_beam_search(d_max, Delta, W=2000, a_max=10):
    B = ceil(d_max * LOG2_3) + Delta
    N0 = 1 << (B - 1)
    U = (1 << B) - 1
    
    # State: (S, c, L, D, path_tuple)
    # We don't store q_min, q_max in the state directly for uniqueness, 
    # but we compute them to check survival and as an objective.
    # Actually, tracking L is enough.
    
    # Initial state
    beam = [(0, 0, N0, 0, ())] # S, c, L, D, path
    
    print(f"\nRunning Beam Search: d_max={d_max}, Delta={Delta} => Target B={B}")
    print(f"{'k':>3} | {'Surviving':>10} | {'G_max':>9} | {'rho_defect_max':>14} | {'q_min_min':>12}")
    print("-" * 65)
    
    for k in range(1, d_max + 1):
        next_states = []
        
        # We use a set to deduplicate identical (S, c, L, D) states
        seen = set()
        
        for S, c, L, D, path in beam:
            for a in range(1, a_max + 1):
                S_new = S + a
                c_new = 3 * c + (1 << S)
                
                # L_new = max(L, floor((2^S_new * N0 - c_new) / 3^k) + 1)
                num = (1 << S_new) * N0 - c_new
                den = 3**k
                L_cand = num // den + 1
                L_new = max(L, L_cand)
                
                if L_new > U:
                    continue # Interval is empty, absolute death
                
                # CRT check
                mod = 1 << (S_new + 1)
                inv3k = pow(3, -k, mod)
                rho = (((1 << S_new) - c_new) * inv3k) % mod
                if rho < 0:
                    rho += mod
                
                q_min = (L_new - rho + mod - 1) // mod
                q_max = (U - rho) // mod
                
                if q_min > q_max:
                    continue # No integer lift in the interval for this prefix
                
                D_new = D + 1 if a >= 3 else D
                
                state_key = (S_new, c_new, L_new, D_new)
                if state_key not in seen:
                    seen.add(state_key)
                    # G_new = k * LOG2_3 - S_new
                    G_new = k * LOG2_3 - S_new
                    next_states.append({
                        'S': S_new, 'c': c_new, 'L': L_new, 'D': D_new, 
                        'path': path + (a,), 'q_min': q_min, 'G': G_new
                    })
                    
        total_surviving = len(next_states)
        if total_surviving == 0:
            print(f"{k:>3} | {0:>10} | {'-':>9} | {'-':>14} | {'-':>12}")
            break
            
        # Sort by the 3 objectives
        # 1. Maximize G
        next_states.sort(key=lambda x: x['G'], reverse=True)
        beam_G = next_states[:W]
        
        # 2. Maximize Defect Density (D)
        next_states.sort(key=lambda x: x['D'], reverse=True)
        beam_D = next_states[:W]
        
        # 3. Minimize q_min
        next_states.sort(key=lambda x: x['q_min'])
        beam_Q = next_states[:W]
        
        # Combine and deduplicate
        combined = { (x['S'], x['c'], x['L'], x['D'], x['path']) 
                     for x in beam_G + beam_D + beam_Q }
        beam = list(combined)
        
        # Metrics for printing
        best_G = max(x['G'] for x in next_states)
        best_rho_D = max(x['D'] for x in next_states) / k
        best_q_min = min(x['q_min'] for x in next_states)
        
        print(f"{k:>3} | {total_surviving:>10} | {best_G:>9.5f} | {best_rho_D:>14.5f} | {best_q_min:>12}")
        
    return next_states if total_surviving > 0 else []

def main():
    print("=" * 80)
    print("G2: SURVIVAL GRAMMAR BEAM SEARCH")
    print("Separating CRT scarcity from dynamic survival via scalable window B.")
    print("=" * 80)
    
    d_max = 50
    W = 1000 # Beam width per objective (total beam size <= 3*W)
    
    # Test different Deltas to see if survival is structurally blocked
    # even when CRT scarcity is completely removed.
    for Delta in [0, 5, 20, 40]:
        t0 = time.time()
        run_beam_search(d_max, Delta, W=W)
        print(f"Time for Delta={Delta}: {time.time()-t0:.2f}s")
        
if __name__ == "__main__":
    main()
