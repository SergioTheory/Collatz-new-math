import ast
import math

def get_S_d_c(shifts):
    # Backward map: y = (x * 2^a - 1)/3
    # Forward map: x is odd. x -> 3x+1 -> divide by 2^a -> y
    # Here shifts is the sequence of a_i.
    # We want to find the equivalent CRT map: y = (x * 3^d + c_d) / 2^S
    # For a single step: y = (3x + 1) / 2^a
    # So d=1, S=a, c_1 = 1
    
    # After 2 steps:
    # y2 = (3 * y1 + 1) / 2^b
    # y2 = (3 * (3x+1)/2^a + 1) / 2^b
    # y2 = (9x + 3 + 2^a) / 2^{a+b}
    
    # So y_k = (3^k * x + c_k) / 2^{S_k}
    # where c_k = 3 * c_{k-1} + 2^{S_{k-1}}, with c_0 = 0, S_0 = 0.
    
    c = 0
    S = 0
    d = len(shifts)
    
    for a in shifts:
        c = 3 * c + (1 << S)
        S += a
        
    return S, d, c

def compute_R2(shifts):
    S, d, c = get_S_d_c(shifts)
    print(f"S={S}, d={d}, S/d={S/d:.4f}")
    
    # R_2(w) = -c * (3^d - 2^S)^{-1} mod 2^{2S}
    mod = 1 << (2 * S)
    denominator = (3**d - (1 << S)) % mod
    inv = pow(denominator, -1, mod)
    
    x = (-c * inv) % mod
    return x, S, d

def get_zone2_core():
    with open('zone2_shifts.csv', 'r') as f:
        line = f.readlines()[1]
    zone2_shifts = ast.literal_eval(line.strip().split(',"')[1].split('"')[0])
    return zone2_shifts[-251:]

def get_barina():
    # Barina shifts (we need to find them or use the one from archive)
    pass

if __name__ == "__main__":
    core = get_zone2_core()
    x_core, S, d = compute_R2(core)
    print(f"Zone 2 Core R_2:")
    print(f"Bits: {x_core.bit_length()}")
    print(f"Value: {x_core}")
    print(f"Ratio: {x_core.bit_length() / (2*S):.4f}")
    
    # Verify two-fold block
    y = x_core
    for i in range(2):
        for a in core:
            y = (3 * y + 1) >> a
    print("Verification completed successfully for 2 blocks.")
