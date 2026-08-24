"""
Experiment 1: Spectral gap of tilted 3-adic reverse operator at n=8.

Purpose: Verify Lemma A3 (uniform spectral gap) at n=8 (4374 states).
Paper's n=7 reference values:
  s=0.0: gap=0.0469, max/min(h)=1289.8
  s=0.1: gap=0.0759, max/min(h)=207.5
  s=0.2: gap=0.1291, max/min(h)=36.7
  s=0.3: gap=0.2152, max/min(h)=9.2
  s=0.4: gap=0.3269, max/min(h)=3.6
  s=0.5: gap=0.4531, max/min(h)=2.0

Expected: gap at n=8 comparable to n=7, confirming uniformity in n.

UNITS: all tilts s in nats (s < ln2 ≈ 0.6931).
The operator is P_n^{(s)}(x,y) with q = e^s / 2.

KEY FIX vs Qwen's draft:
  - Use mod_high = 3^{n+1} for correct modular division by 3
  - Column indices via state-to-index mapping (not raw modular values)
"""

import numpy as np
from scipy import linalg
import time
import sys

def build_and_analyze(n_val):
    """Build the tilted operator at scale n and compute spectral data."""
    
    mod = 3**n_val
    mod_high = 3**(n_val + 1)  # for exact division by 3
    T = 2 * 3**(n_val - 1)    # order of 2 in (Z/3^n Z)*
    
    print(f"\n{'='*60}")
    print(f"n = {n_val}, mod = {mod}, T = {T}, states = {2*3**(n_val-1)}")
    print(f"{'='*60}")
    
    # Precompute powers of 2 mod 3^{n+1}
    pow2h = np.zeros(T + 1, dtype=np.int64)
    pow2h[0] = 1
    for a in range(1, T + 1):
        pow2h[a] = (pow2h[a-1] * 2) % mod_high
    
    # States: all x in [0, mod) with x % 3 != 0
    states = np.array([x for x in range(mod) if x % 3 != 0], dtype=np.int64)
    N = len(states)
    print(f"Number of states: {N}")
    
    # State-to-index mapping
    s2i = -np.ones(mod, dtype=np.int64)
    for i in range(N):
        s2i[states[i]] = i
    
    # Precompute valid a-values for each parity class
    # x ≡ 1 (mod 3): even a needed (2^a ≡ 1 ≡ x^{-1} mod 3)
    # x ≡ 2 (mod 3): odd a needed  (2^a ≡ 2 ≡ x^{-1} mod 3)
    a_even = np.arange(2, T + 1, 2, dtype=np.int64)  # [2, 4, ..., T]
    a_odd  = np.arange(1, T + 1, 2, dtype=np.int64)  # [1, 3, ..., T-1]
    
    p2h_even = pow2h[a_even]  # 2^a mod 3^{n+1} for even a
    p2h_odd  = pow2h[a_odd]   # 2^a mod 3^{n+1} for odd a
    
    s_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    
    print(f"\n{'s':>4} | {'rho':>12} | {'|lambda_2|':>12} | {'gap':>8} | {'max/min(h)':>12}")
    print("-" * 60)
    
    results = []
    
    for s_val in s_values:
        q = np.exp(s_val) / 2.0
        qT = q ** T
        norm = 1.0 / (1.0 - qT)
        
        # Precompute weights
        w_even = norm * q ** a_even.astype(np.float64)
        w_odd  = norm * q ** a_odd.astype(np.float64)
        
        # Build dense matrix P[i, j]
        P = np.zeros((N, N), dtype=np.float64)
        
        t0 = time.time()
        for i in range(N):
            x = int(states[i])
            if x % 3 == 1:
                p2 = p2h_even
                w = w_even
            else:
                p2 = p2h_odd
                w = w_odd
            
            # y = (2^a * x - 1) / 3 mod 3^n
            # Use mod_high for exact division:
            # val = (2^a * x) mod 3^{n+1}, then (val - 1) // 3 is exact, reduce mod 3^n
            vals = (p2.astype(np.int64) * x) % mod_high
            y_vals = ((vals - 1) // 3) % mod
            
            # Map to state indices
            j_vals = s2i[y_vals]
            valid = j_vals >= 0  # y must be non-zero mod 3
            
            # Accumulate
            np.add.at(P[i], j_vals[valid], w[valid])
        
        build_time = time.time() - t0
        
        # Eigenvalue computation
        t1 = time.time()
        eigenvalues = linalg.eigvals(P)
        eigen_time = time.time() - t1
        
        # Sort by magnitude
        ev_abs = np.abs(eigenvalues)
        order = np.argsort(-ev_abs)
        rho = ev_abs[order[0]]
        l2 = ev_abs[order[1]]
        gap = 1.0 - l2 / rho
        
        # For eigenvector ratio, use power method (cheaper than full eig)
        t2 = time.time()
        h = np.ones(N) / N
        for _ in range(500):
            h_new = P.T @ h
            h_new /= np.max(h_new)
            if np.max(np.abs(h_new - h)) < 1e-12:
                break
            h = h_new
        h = h_new
        h_positive = h[h > 1e-15]
        if len(h_positive) > 0:
            ratio = np.max(h_positive) / np.min(h_positive)
        else:
            ratio = float('inf')
        pm_time = time.time() - t2
        
        print(f"{s_val:4.1f} | {rho:12.6f} | {l2:12.6f} | {gap:8.4f} | {ratio:12.1f}")
        
        results.append({
            's': s_val, 'rho': rho, 'l2': l2, 'gap': gap,
            'ratio': ratio, 'build': build_time, 'eigen': eigen_time
        })
    
    print(f"\nTimings: build={results[0]['build']:.1f}s, eigen={results[0]['eigen']:.1f}s per s-value")
    return results


if __name__ == "__main__":
    print("Experiment 1: Spectral gap of tilted 3-adic reverse operator")
    print("Verifying Lemma A3 uniformity across n")
    
    # First do n=7 to reproduce paper's values (sanity check)
    print("\n*** SANITY CHECK: n=7 (should match paper) ***")
    res7 = build_and_analyze(7)
    
    # Then n=8 (the new result)
    print("\n*** NEW COMPUTATION: n=8 ***")
    res8 = build_and_analyze(8)
    
    # Comparison
    print("\n\n" + "="*60)
    print("COMPARISON: n=7 vs n=8")
    print("="*60)
    print(f"{'s':>4} | {'gap(n=7)':>10} | {'gap(n=8)':>10} | {'ratio(7)':>10} | {'ratio(8)':>10}")
    print("-" * 55)
    for r7, r8 in zip(res7, res8):
        print(f"{r7['s']:4.1f} | {r7['gap']:10.4f} | {r8['gap']:10.4f} | {r7['ratio']:10.1f} | {r8['ratio']:10.1f}")
    
    print("\nIf gaps at n=8 >= gaps at n=7 on [0.1, 0.5], Lemma A3 is supported.")
    print("If max/min(h) at n=8 is bounded, eigenfunction uniformity is confirmed.")
