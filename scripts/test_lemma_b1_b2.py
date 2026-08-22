import ast
import math

def test_b1_b2():
    # Load Zone 2 core shifts
    with open('zone2_shifts.csv', 'r') as f:
        line = f.readlines()[1]
    zone2_shifts = ast.literal_eval(line.strip().split(',"')[1].split('"')[0])
    core_shifts = zone2_shifts[-251:]
    
    # Reverse shifts for inverse orbit
    bwd_shifts = core_shifts[::-1]
    
    print("--- LEMMA B1: Vacuum (2,1,1) Shadow Comparison ---")
    print("First 30 shifts of inverse orbit:")
    print("Actual:  ", bwd_shifts[:30])
    
    # The vacuum period for inverse orbit is (1,1,2) because forward is (2,1,1).
    # Wait, the user said: "прямой shift-вектор вакуума — период (2,1,1) с плотностью сдвигов ровно 4/3."
    # Let's check the algebraic proof: 
    # xi = -29/11. 3*xi+1 = -76/11 -> a0 = v2(-76) = 2.
    # Next: (-76/11) / 4 = -19/11 -> a1 = 1.
    # Next: 3*(-19/11)+1 = -46/11 -> divide by 2 -> -23/11 -> a2 = 1.
    # So forward shifts from -29/11 are exactly 2, 1, 1...
    # The reverse shifts would be 1, 1, 2...
    vacuum_rev = ([1, 1, 2] * 10)[:30]
    print("Vacuum:  ", vacuum_rev)
    
    matches = sum(1 for i in range(30) if bwd_shifts[i] == vacuum_rev[i])
    print(f"Matches in first 30: {matches}/30")
    
    print("\n--- LEMMA B2: Gain/Charge Balance ---")
    d = len(core_shifts)
    S = sum(core_shifts)
    print(f"d = {d}, S = {S}")
    
    # Delta (sum of excess shifts relative to vacuum)
    delta = S - (4/3)*d
    print(f"Delta (excess S vs vacuum): {delta:.4f}")
    
    # Theoretical gain formula: G(d) = d * log2(3) - S
    G_d = d * math.log2(3) - S
    print(f"Total Gain G(d): {G_d:.4f}")
    
    # Boundary condition balance: G* = P - B
    # For Zone 2: P = 140 (approx 139.x peak bits), B = 72 (or 71 bits)
    # The exact boundary conditions:
    P = 139.73 # approx for peak
    B = 71.36 # approx for base
    print(f"Boundary gap (P - B) is approx {P - B:.4f}")
    
    # G(d) = d*(log2(3) - 4/3) - delta
    G_theoretical = d * (math.log2(3) - 4/3) - delta
    print(f"G(d) via Lemma B2: {G_theoretical:.4f}")
    
    print(f"d*(log2(3) - 4/3) = {d * (math.log2(3) - 4/3):.4f}")
    print(f"delta = {delta:.4f}")

if __name__ == "__main__":
    test_b1_b2()
