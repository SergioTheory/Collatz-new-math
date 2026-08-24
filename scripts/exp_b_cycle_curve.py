"""
Experiment B: Cycle size frontier curve
Compute the exact upper bound for cycle size N vs d up to d=10^8
and compare with the verification frontier 2^68.
"""
from mpmath import mp, log, floor, power
import time

def main():
    mp.dps = 200
    log2_3 = log(3) / log(2)
    frontier_bits = 68.0
    
    x = log2_3
    a = int(floor(x))
    frac = x - a
    p0, q0 = mp.mpf(1), mp.mpf(0)
    p1, q1 = mp.mpf(a), mp.mpf(1)
    
    print("Experiment B: Cycle Size Upper Bounds vs Cycle Length (d)")
    print(f"{'d (cycle len)':>15} | {'S (total shift)':>15} | {'Max cycle N (bits)':>20} | {'Status vs 2^68':>15}")
    print("-" * 75)
    
    max_d = 10**9
    
    while q1 <= max_d:
        p_int = int(p1)
        q_int = int(q1)
        
        residual = abs(mp.mpf(p_int) - mp.mpf(q_int) * log2_3)
        if residual == 0.0:
            break
            
        log2_diff = float(p_int) + float(log(residual * log(2)) / log(2))
        max_N_bits = float(p_int) - log2_diff
        
        status = "Excluded" if max_N_bits < frontier_bits else "OPEN"
        
        print(f"{q_int:15d} | {p_int:15d} | {max_N_bits:20.1f} | {status:>15}")
        
        if max_N_bits >= frontier_bits:
            print("\n>>> Frontier breached at this d!")
            break
            
        if abs(frac) < 1e-150:
            break
            
        frac = 1 / frac
        a = int(floor(frac))
        frac = frac - a
        
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0

if __name__ == "__main__":
    main()
