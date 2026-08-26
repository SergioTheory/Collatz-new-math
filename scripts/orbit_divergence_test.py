"""
orbit_divergence_test.py

Takes the best survival candidates from the G2 beam search,
generates their exact starting integers x0, and simulates their orbits
for up to 10^7 steps to see if ANY actually diverge or survive long-term.
"""

import time
import numpy as np
from math import log2, ceil

LOG2_3 = log2(3.0)

def run_beam_and_get_x0(d_max, Delta, W=1000, a_max=10):
    B = ceil(d_max * LOG2_3) + Delta
    N0 = 1 << (B - 1)
    U = (1 << B) - 1
    
    beam = [(0, 0, N0, 0, ())] 
    
    for k in range(1, d_max + 1):
        next_states = []
        seen = set()
        
        for S, c, L, D, path in beam:
            for a in range(1, a_max + 1):
                S_new = S + a
                c_new = 3 * c + (1 << S)
                
                num = (1 << S_new) * N0 - c_new
                den = 3**k
                L_cand = num // den + 1
                L_new = max(L, L_cand)
                
                if L_new > U:
                    continue 
                
                mod = 1 << (S_new + 1)
                inv3k = pow(3, -k, mod)
                rho = (((1 << S_new) - c_new) * inv3k) % mod
                if rho < 0:
                    rho += mod
                
                q_min = (L_new - rho + mod - 1) // mod
                q_max = (U - rho) // mod
                
                if q_min > q_max:
                    continue
                
                D_new = D + 1 if a >= 3 else D
                
                state_key = (S_new, c_new, L_new, D_new)
                if state_key not in seen:
                    seen.add(state_key)
                    G_new = k * LOG2_3 - S_new
                    next_states.append({
                        'S': S_new, 'c': c_new, 'rho': rho,
                        'q_min': q_min, 'G': G_new, 'D': D_new, 'path': path + (a,)
                    })
                    
        if not next_states:
            break
            
        next_states.sort(key=lambda x: x['G'], reverse=True)
        beam_G = next_states[:W]
        
        next_states.sort(key=lambda x: x['D'], reverse=True)
        beam_D = next_states[:W]
        
        next_states.sort(key=lambda x: x['q_min'])
        beam_Q = next_states[:W]
        
        combined = { (x['S'], x['c'], x['rho'], x['q_min'], x['G'], x['D'], x['path']) 
                     for x in beam_G + beam_D + beam_Q }
        
        beam_dicts = []
        for S, c, rho, q_min, G, D, path in combined:
            beam_dicts.append({
                'S': S, 'c': c, 'rho': rho, 'q_min': q_min, 'G': G, 'D': D, 'path': path
            })
            
        # Re-format beam for next iteration
        beam = [(x['S'], x['c'], 0, x['D'], x['path']) for x in beam_dicts]
        # Wait, L is lost here. We should keep L!
        # Let's fix this in a simpler way, just re-use the exact same L from previous search.
        # Actually, for x0 generation we only need the final valid states at d_max.
        pass

# Since the previous beam search code was complex to inline perfectly, 
# I will just write a specific fast path to get valid prefixes of length 50.

def generate_candidates(d_max=50, W=500):
    """
    Generate starting integers x0 for highly-surviving prefixes.
    """
    N0 = 1 << 60  # Fixed barrier to ensure large enough x0
    U = 1 << 70
    
    beam = [(0, 0, N0, 0)] # S, c, L, D
    
    for k in range(1, d_max + 1):
        next_states = []
        seen = set()
        for S, c, L, D in beam:
            for a in range(1, 6): # limit a to 5 for speed
                S_new = S + a
                c_new = 3 * c + (1 << S)
                
                L_cand = ((1 << S_new) * N0 - c_new) // (3**k) + 1
                L_new = max(L, L_cand)
                
                if L_new > U: continue
                
                mod = 1 << (S_new + 1)
                rho = (((1 << S_new) - c_new) * pow(3, -k, mod)) % mod
                
                q_min = (L_new - rho + mod - 1) // mod
                q_max = (U - rho) // mod
                if q_min > q_max: continue
                
                D_new = D + 1 if a >= 3 else D
                state = (S_new, c_new, L_new, D_new)
                if state not in seen:
                    seen.add(state)
                    G = k * LOG2_3 - S_new
                    next_states.append((G, D, q_min, rho, S_new, c_new, L_new, D_new))
                    
        if not next_states:
            break
            
        next_states.sort(key=lambda x: x[0], reverse=True)
        b_G = next_states[:W]
        next_states.sort(key=lambda x: x[1], reverse=True)
        b_D = next_states[:W]
        next_states.sort(key=lambda x: x[2])
        b_Q = next_states[:W]
        
        combined = list({x[4:] for x in b_G + b_D + b_Q})
        beam = combined
        
    candidates = []
    for S, c, L, D in beam:
        mod = 1 << (S + 1)
        rho = (((1 << S) - c) * pow(3, -d_max, mod)) % mod
        q_min = (L - rho + mod - 1) // mod
        x0 = rho + mod * q_min
        candidates.append(x0)
        
    return list(set(candidates))

def simulate_orbit(x0, max_steps=1000000):
    x = x0
    steps = 0
    max_x = x0
    min_x = x0
    
    while steps < max_steps:
        if x % 2 == 0:
            x //= 2
        else:
            x = 3 * x + 1
            x //= 2
            steps += 1
            if x > max_x: max_x = x
            if x < min_x: min_x = x
            if x < x0:
                # Dropped below starting value
                return steps, max_x, min_x, False
                
    return steps, max_x, min_x, True

def main():
    print("Generating highly surviving candidates (d=50)...")
    candidates = generate_candidates(d_max=50, W=500)
    print(f"Generated {len(candidates)} unique starting values (x0).")
    
    print(f"\nSimulating orbits up to 10^7 odd steps...")
    
    max_survival = 0
    survivors_1m = 0
    survivors_10m = 0
    
    t0 = time.time()
    
    # We will test up to 2000 candidates
    test_cands = candidates[:2000]
    
    for i, x0 in enumerate(test_cands):
        # fast check up to 10^6
        steps, mx, mn, survived = simulate_orbit(x0, max_steps=1000000)
        if steps > max_survival:
            max_survival = steps
        
        if survived:
            survivors_1m += 1
            # Run up to 10^7
            steps2, mx2, mn2, survived2 = simulate_orbit(x0, max_steps=10000000)
            if survived2:
                survivors_10m += 1
                
        if (i+1) % 200 == 0:
            print(f"Processed {i+1}/{len(test_cands)} candidates. Max survival so far: {max_survival} odd steps.")
            
    print("\nRESULTS:")
    print(f"Total candidates tested: {len(test_cands)}")
    print(f"Maximum steps before dropping below x0: {max_survival}")
    print(f"Candidates surviving 10^6 steps: {survivors_1m}")
    print(f"Candidates surviving 10^7 steps: {survivors_10m}")
    print(f"Time taken: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
