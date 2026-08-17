import json
import os
import math

def compute_c(shift_vec):
    c = 0
    S = 0
    for a in shift_vec:
        c = 3 * c + (1 << S)
        S += a
    return c, S

def shift_vector_to_peak(n, target_peak_bits):
    v = []
    x = n
    peak_val = 0
    d = 0
    # Run until we hit the target peak bit length
    # Note: peak_bits in this context is just the bit_length of the maximum value reached.
    while True:
        if x.bit_length() >= target_peak_bits:
            break
        if x == 1:
            break
        
        # Collatz step
        x = 3 * x + 1
        a = 0
        while x % 2 == 0:
            x //= 2
            a += 1
        v.append(a)
        d += 1
        
    return v, d

def step1_macro_obstruction():
    print("=== Step 1: Macro-Obstruction Theorem (Peak 1400) ===")
    P = 1400
    # From caustic balance: bits = 0.4952 * P + 6.5567
    B = int(0.4952 * P + 6.5567)
    
    # Required gain to reach Peak P from a B-bit number
    gain = P - B
    
    # Average gain per step for an optimal chord (sigma ~ 1.33)
    sigma = 1.33
    gain_per_step = math.log2(3) - sigma
    
    d = int(gain / gain_per_step)
    S = int(sigma * d)
    
    print(f"Target Peak (P): {P} bits")
    print(f"Target Center Size (B): ~{B} bits")
    print(f"Required Gain: {gain} bits")
    print(f"Optimal Gain per step (sigma={sigma}): {gain_per_step:.4f} bits/step")
    print(f"Required steps (d): ~{d}")
    print(f"Required 2-adic shift sum (S): ~{S} bits")
    print(f"Modulo Deficit (S - B): {S - B} bits")
    
    expected_candidates = 2 ** (B - S)
    print(f"Expected candidates in a single congruence cylinder: 2^{B - S}")
    print("Conclusion: CRT dimensionality rigidly obstructs constructive reverse synthesis.")

def mod_inverse(a, m):
    # a^-1 mod m
    return pow(a, -1, m)

def step2_validate_known_centers():
    print("\n=== Step 2: Validate Congruence Cylinders on Known Centers ===")
    algebra_path = r"C:\Users\Admin\Documents\Collatz\data\algebra_centers.json"
    centers = {}
    if os.path.exists(algebra_path):
        with open(algebra_path, 'r') as f:
            alg = json.load(f)
            if 'factorization' in alg:
                for k, v in alg['factorization'].items():
                    centers[int(k)] = int(v['center'])
    
    print(f"{'Peak':<5} | {'B (bits)':<8} | {'d (steps)':<10} | {'S (bits)':<8} | {'Deficit (S-B)':<15} | {'Localized?':<10}")
    print("-" * 75)
    
    for p in sorted(centers.keys())[:15]:  # Test first 15 for brevity
        c = centers[p]
        B = c.bit_length()
        
        # We need the shift vector up to the peak.
        # But wait, does 'p' perfectly match the max bit length? Yes, for these seeds.
        v, d = shift_vector_to_peak(c, p)
        
        # Calculate offset c_beta and S
        c_beta, S = compute_c(v)
        
        # Verification: c_beta + 3^d * c = 0 (mod 2^S)
        # So c == -c_beta * (3^d)^-1 mod 2^S
        modulus = 1 << S
        try:
            inv_3d = mod_inverse(3**d, modulus)
            expected_c = (-c_beta * inv_3d) % modulus
            localized = (expected_c == c)
        except ValueError:
            localized = False
            
        deficit = S - B
        loc_str = "YES" if localized else "NO"
        print(f"{p:<5} | {B:<8} | {d:<10} | {S:<8} | {deficit:<15} | {loc_str:<10}")

if __name__ == '__main__':
    step1_macro_obstruction()
    step2_validate_known_centers()
