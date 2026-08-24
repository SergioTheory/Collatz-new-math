"""
Experiment F2: Frobenius-Perron operator for the Collatz Skew Product
Computes the invariant joint measure of (h, u, v) = (frac(log2 N), N mod 2^m, N mod 3^n)
to explain the "magic" bias observed in Experiment F.
"""

import numpy as np
from scipy import stats
import time

def collatz_orbit_odd(N, max_steps):
    orb = []
    x = N
    for _ in range(max_steps):
        if x % 2 == 0:
            x //= 2
        else:
            orb.append(x)
            x = 3 * x + 1
            if x == 4:
                break
    return orb

def main():
    print("Experiment F2: Frobenius-Perron Invariant Measure")
    
    # 1. Generate empirical data (same as F) to compare
    import random
    random.seed(42)
    seeds = [random.randint(2**50, 2**51) for _ in range(100)]
    full_orb = []
    for s in seeds:
        full_orb.extend(collatz_orbit_odd(int(s), 5000))
        
    M = 8  # 2-adic precision for FP (gives exact a up to a=M)
    M_obs = 3 # 2^3 = 8
    n3 = 2  # 3^2 = 9
    NB = 200 # Height bins
    
    # Precompute valid odd states for mod 2^M
    odds_M = [x for x in range(2**M) if x % 2 != 0]
    idx_M = {x: i for i, x in enumerate(odds_M)}
    
    # Valid states for mod 3^n
    valid_3 = [x for x in range(3**n3) if x % 3 != 0]
    idx_3 = {x: i for i, x in enumerate(valid_3)}
    
    N_u = len(odds_M)
    N_v = len(valid_3)
    
    # FP state: rho[u_idx, v_idx, h_bin]
    rho = np.full((N_u, N_v, NB), 1.0 / (N_u * N_v * NB))
    
    L23 = np.log2(3.0)
    
    # Transition matrix precomputation to speed up FP
    # transitions[u_idx][v_idx] = list of (prob, u_next_idx, v_next_idx, a)
    transitions = [[[] for _ in range(N_v)] for _ in range(N_u)]
    
    for u in odds_M:
        uidx = idx_M[u]
        # find valuation a
        val3u1 = 3 * u + 1
        a = 0
        temp = val3u1
        while temp % 2 == 0 and a < M:
            a += 1
            temp //= 2
            
        if a < M:
            # a is exact. The next u' is determined up to the missing 'a' bits.
            # val3u1 / 2^a is known mod 2^{M-a}.
            base_u_next = temp % (2**(M-a))
            # The missing 'a' bits can take 2^a possible values, uniformly.
            prob = 1.0 / (2**a)
            next_us = [base_u_next + k * (2**(M-a)) for k in range(2**a)]
            
            for v in valid_3:
                vidx = idx_3[v]
                # v' = (3v+1) * 2^{-a} mod 3^n
                # inverse of 2 mod 9 is 5
                inv2 = 5
                v_next = ((3 * v + 1) * (inv2 ** a)) % (3**n3)
                if v_next % 3 == 0:
                    # Should not happen for valid odd steps, but 3v+1 can be 0 mod 9 if v=3, but v%3!=0
                    # Wait, 3v+1 mod 3 is 1. It's never 0 mod 3!
                    pass
                vnext_idx = idx_3[v_next]
                
                for unext in next_us:
                    transitions[uidx][vidx].append((prob, idx_M[unext], vnext_idx, a))
        else:
            # a >= M. Truncate at M. This is rare (prob 2^{-M}).
            # Assume a=M, and next u is uniform over all odds.
            prob = 1.0 / N_u
            a_eff = M
            for v in valid_3:
                vidx = idx_3[v]
                inv2 = 5
                v_next = ((3 * v + 1) * (inv2 ** a_eff)) % (3**n3)
                vnext_idx = idx_3[v_next]
                for unext in odds_M:
                    transitions[uidx][vidx].append((prob, idx_M[unext], vnext_idx, a_eff))

    print("Iterating Frobenius-Perron operator...")
    for it in range(50):
        new_rho = np.zeros_like(rho)
        for uidx in range(N_u):
            for vidx in range(N_v):
                if np.sum(rho[uidx, vidx]) == 0:
                    continue
                for prob, unext, vnext, a in transitions[uidx][vidx]:
                    # shift h by log2(3) - a
                    shift = (L23 - a) * NB
                    # We can use fractional shift or just integer bin shift
                    s_int = int(np.floor(shift))
                    
                    # roll the density
                    shifted_h = np.roll(rho[uidx, vidx], s_int)
                    new_rho[unext, vnext] += prob * shifted_h
        rho = new_rho / np.sum(new_rho)

    # Now marginalize rho down to observed m=3, n=2
    # u mod 8 has 4 states (1,3,5,7)
    obs_odds = [1, 3, 5, 7]
    idx_obs = {x: i for i, x in enumerate(obs_odds)}
    
    fp_means = {}
    for u_obs in obs_odds:
        for v in valid_3:
            # sum over all u in odds_M such that u % 8 == u_obs
            sub_rho = np.zeros(NB)
            for u in odds_M:
                if u % 8 == u_obs:
                    sub_rho += rho[idx_M[u], idx_3[v]]
            
            # compute mean of h
            sub_rho /= np.sum(sub_rho)
            h_vals = np.linspace(0, 1, NB, endpoint=False) + 0.5/NB
            mean_h = np.sum(sub_rho * h_vals)
            fp_means[(u_obs, v)] = mean_h
            
    # Empirical
    emp_states = {}
    for val in full_orb:
        y = val % 8
        z = val % 9
        h = np.log2(float(val)) % 1.0
        state = (y, z)
        if state not in emp_states:
            emp_states[state] = []
        emp_states[state].append(h)
        
    print("\nComparison of E[frac(log2 N)] by State (u mod 8, v mod 9):")
    print(f"{'u':>3} | {'v':>3} | {'Count':>7} | {'Empirical Mean':>15} | {'FP Mean':>15} | {'Diff':>10}")
    print("-" * 65)
    
    sorted_states = sorted(emp_states.items(), key=lambda item: len(item[1]), reverse=True)
    
    for state, vals in sorted_states:
        u, v = state
        count = len(vals)
        if count < 10:
            continue
        emp_mean = np.mean(vals)
        fp_mean = fp_means.get(state, 0.0)
        diff = abs(emp_mean - fp_mean)
        
        print(f"{u:3d} | {v:3d} | {count:7d} | {emp_mean:15.4f} | {fp_mean:15.4f} | {diff:10.4f}")

if __name__ == "__main__":
    main()
