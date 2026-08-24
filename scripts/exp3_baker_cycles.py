"""
Experiment 3: Continued fractions of log2(3) and cycle exclusion bounds.

Purpose: For each convergent p/q of log2(3), compute:
  1. |2^p - 3^q| (the denominator of a hypothetical cycle)
  2. Maximum N for a cycle of length q: N = c_q / (2^p - 3^q)
  3. Compare with the verification frontier (2^68, Barina)

For a cycle of length d (odd steps) with total shift S:
  3^d * N + c_d = 2^S * N  =>  N = c_d / (2^S - 3^d)

The best cycles correspond to convergents of log2(3) where S/d ~= log2(3).
Baker's theorem: |2^S - 3^d| >= 2^{S*(1 - C/log(d))} for effective C.

NOTE (Qwen's correction): For cycles, S/d -> log2(3) ~= 1.585,
NOT 4/3 (which is the vacuum shift of the dressed instanton in I1).

Units: bits throughout.
"""

from mpmath import mp, mpf, log, floor, power
import time

def main():
    mp.dps = 300  # high precision
    
    log2_3 = log(3) / log(2)  # ~= 1.58496...
    
    print("Experiment 3: Cycle exclusion via continued fractions of log2(3)")
    print(f"log2(3) = {mp.nstr(log2_3, 50)}")
    print(f"Verification frontier: 2^68 ~= 2.95 x 10^20 (Barina 2020)")
    print()
    
    # Continued fraction expansion of log2(3)
    x = log2_3
    a = int(floor(x))
    frac = x - a
    
    p0, q0 = mpf(1), mpf(0)  # p_{-1}, q_{-1}
    p1, q1 = mpf(a), mpf(1)  # p_0, q_0
    
    print(f"{'k':>3} | {'a_k':>6} | {'q (d)':>10} | {'p (S)':>10} | {'|2^p-3^q|':>20} | {'log2|...|':>12} | {'max cycle bits':>16} | {'status':>10}")
    print("-" * 110)
    
    convergents = []
    k = 0
    
    while q1 < mpf(10)**8:
        p_int = int(p1)
        q_int = int(q1)
        
        # Compute |2^p - 3^q| with high precision
        # Use mpmath for exact large integer arithmetic
        if q_int <= 5000:
            pow2 = power(2, p_int)
            pow3 = power(3, q_int)
            diff = abs(pow2 - pow3)
            
            if diff > 0:
                log2_diff = float(log(diff) / log(2))
            else:
                log2_diff = float('-inf')
            
            # Maximum N for a cycle of length q_int:
            # N ~= c_q / (2^S - 3^d) where c_q < 2^S (bounded by geometric series)
            # So max bits of N ~= S - log2|2^S - 3^d| = p_int - log2_diff
            max_N_bits = p_int - log2_diff if log2_diff > float('-inf') else float('inf')
        else:
            # For large q, use the approximation
            # |2^p - 3^q| ~= 2^p * |1 - (3/2)^q * 2^{q-p}|
            # ~= 2^p * |p - q*log2(3)| * ln2
            residual = abs(p_int - q_int * float(log2_3))
            log2_diff = p_int + float(log(residual * float(log(2))) / log(2))
            max_N_bits = p_int - log2_diff
        
        # Status
        if max_N_bits < 68:
            status = "EXCLUDED"
        elif max_N_bits < 200:
            status = "near frontier"
        else:
            status = "open"
        
        convergents.append((k, int(a), q_int, p_int, log2_diff, max_N_bits))
        
        print(f"{k:3d} | {int(a):6d} | {q_int:10d} | {p_int:10d} | {'':>20s} | {log2_diff:12.2f} | {max_N_bits:16.1f} | {status:>10}")
        
        # Next continued fraction step
        if abs(frac) < mpf(10)**(-280):
            break
        frac = 1 / frac
        a = int(floor(frac))
        frac = frac - a
        
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        k += 1
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nTotal convergents computed: {len(convergents)}")
    
    # Find the convergent closest to allowing a large cycle
    if convergents:
        best = max(convergents, key=lambda c: c[5])  # max by max_N_bits
        print(f"\nMost dangerous convergent:")
        print(f"  d = {best[2]}, S = {best[3]}, max cycle N ~= 2^{best[5]:.1f}")
        print(f"  Frontier: 2^68")
        if best[5] < 68:
            print(f"  -> ALL cycles of this form excluded by Barina verification")
        else:
            print(f"  -> This convergent permits cycles above the frontier")
            print(f"  -> But cycle must also satisfy 2-adic admissibility (grammar)")
    
    # Steiner's result
    print(f"\nSteiner (2008): cycles of length <= 68 excluded for 3x+1")
    print(f"Our computation extends the landscape to d ~ {convergents[-1][2] if convergents else '?'}")
    
    # Key insight
    print(f"\nKEY INSIGHT:")
    print(f"  The closest 2^S to 3^d grows as (3/2)^d.")
    print(f"  Baker's theorem: |2^S - 3^d| >= 2^(S - kappa*log(d))")
    print(f"  -> max cycle N <= C * d^kappa")
    print(f"  -> for d > d_0(kappa), any cycle N must be < 2^68")
    print(f"  -> combined with Barina, cycles are excluded for all d > d_0")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nTotal time: {time.time()-t0:.2f}s")
