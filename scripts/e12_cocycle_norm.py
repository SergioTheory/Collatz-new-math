import numpy as np

def compute_cocycle_norm(d_max, xi_0):
    # State space size: max S is d_max * 10
    S_max = d_max * 10
    V = np.zeros(S_max, dtype=np.complex128)
    V[0] = 1.0 + 0j
    
    norms = []
    
    for j in range(1, d_max + 1):
        xi_j = (xi_0 * (3**(d_max - j))) % 1.0
        
        next_V = np.zeros(S_max, dtype=np.complex128)
        
        # V_j(S) = sum_{S' < S} V_{j-1}(S') * (1/2)^{S-S'} * exp(-2pi i xi_j 2^S)
        # We can optimize this by maintaining a prefix sum!
        # prefix_sum = sum_{S' < S} V_{j-1}(S') * (1/2)^{-S'}
        # Then next_V[S] = prefix_sum * (1/2)^S * exp(...)
        
        prefix_sum = 0j
        for S in range(1, S_max):
            # add the S-1 term to prefix
            # wait, (1/2)^{-S'} is 2^{S'}, which overflows.
            # Instead, just do the O(S_max * a_max) loop since a_max is small.
            pass
            
        # O(S_max * a_max) loop
        a_max = 50
        for S in range(1, S_max):
            sum_val = 0j
            for a in range(1, min(S, a_max) + 1):
                S_prime = S - a
                sum_val += V[S_prime] * (0.5 ** a)
            
            # For 2^S * xi_j mod 1, 2^S can be very large.
            # However, xi_j has a fixed denominator if it's rational, or we can just compute it.
            # If xi_j = K / 2^B, then for S >= B, 2^S xi_j = 0 mod 1.
            # So phase is 0 for S >= B.
            # Let's just use a general float xi_j. But 2^S * xi_j mod 1 requires arbitrary precision if S is large and xi_j is a general float.
            # Wait, if xi_0 = H / 65536, then xi_j = H * 3^{d-j} / 65536.
            # Then 2^S * xi_j = H * 3^{d-j} * 2^S / 65536.
            # This is exactly modulo 1. We can compute (H * 3^{d-j} * (2**S % 65536)) % 65536 / 65536.
            # This is perfectly exact!
            
            H = int(xi_0 * 65536)
            phase_num = (H * pow(3, d_max - j, 65536) * pow(2, S, 65536)) % 65536
            phase = 2 * np.pi * phase_num / 65536.0
            
            next_V[S] = sum_val * np.exp(-1j * phase)
            
        V = next_V
        current_norm = np.sum(np.abs(V))
        norms.append(current_norm)
        
    return norms

print("=== Cocycle Norm Decay ===")
for H in [1, 3, 137, 1000]:
    print(f"\n--- Frequency xi_0 = {H}/65536 ---")
    for d in [50, 100, 200, 400, 800]:
        norms = compute_cocycle_norm(d, H / 65536.0)
        norm_val = norms[-1]
        decay = norm_val**(1.0/d)
        print(f"d = {d:3d}: final norm = {norm_val:.6e}, decay per step = {decay:.4f}")

