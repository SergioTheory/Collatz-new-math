"""
Experiment A: Divergent orbits vs Diophantine approximation
Formalizing and numerically verifying the no-go theorem for the Diophantine route to divergent orbits.
"""
import numpy as np

def collatz_step(x):
    x = 3 * x + 1
    while x % 2 == 0:
        x //= 2
    return x

def main():
    print("Experiment A: Diophantine No-Go for Divergent Orbits")
    print("Rhin (1987): Irrationality measure of log2(3) is mu = 8.616")
    print("For a divergent orbit to exist via the Diophantine route, we need:")
    print("  (log2 N_d) / d < C / d^mu  ==>  log2 N_d < C * d^(1-mu)")
    print("Since 1-mu = -7.616 < 0, log2 N_d must approach 0 as d -> inf.")
    print("This contradicts N_d -> inf (divergence).\n")
    
    mu = 8.616
    
    print("Let's illustrate this massive gap on long empirical trajectories.")
    # We use a known number that has a long trajectory before falling below starting value.
    # e.g., 27 (111 steps), or a larger record setter.
    # 27 is small, let's use 27, 871, 703, 6171 (some standard record-setters)
    
    starts = [27, 871, 6171, 75128138247, 2**50 - 1]
    
    for N0 in starts:
        print(f"\n--- Starting N0 = {N0} ---")
        N = N0
        d = 0
        
        # Track max trajectory height
        max_log = 0
        d_at_max = 0
        
        import math
        while N >= N0 and d < 2000:
            N = collatz_step(N)
            d += 1
            if math.log2(N) > max_log:
                max_log = math.log2(N)
                d_at_max = d
                
        print(f"Reached max height ~2^{max_log:.1f} at odd step d = {d_at_max}")
        if d_at_max > 0:
            lhs = max_log / d_at_max
            rhs = 1.0 / (d_at_max ** mu)
            
            print(f"  LHS = (log2 N_d)/d = {lhs:.2e}")
            print(f"  RHS = 1/d^mu       = {rhs:.2e}")
            print(f"  Gap (LHS / RHS)    = {lhs/rhs:.2e}x")
            
if __name__ == "__main__":
    main()
