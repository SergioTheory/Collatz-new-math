import numpy as np

def compute_I_h_naive(M, h):
    K = 1 << M
    
    def get_c_d(word):
        d = len(word)
        c = 3**(d-1)
        S = 0
        for j in range(1, d):
            S += word[j-1]
            c += (3**(d-1-j)) * (2**S)
        return c

    def generate_compositions(M):
        if M == 0:
            yield []
            return
        for i in range(1, M + 1):
            for tail in generate_compositions(M - i):
                yield [i] + tail
                
    total_sum = 0j
    for w in generate_compositions(M):
        d = len(w)
        inv3 = pow(3, -d, 1 << (M+1))
        c_d = get_c_d(w)
        
        rho_w = ((1 << M) - c_d) * inv3 % (1 << (M+1))
        assert rho_w % 2 == 1
        r_w = (rho_w - 1) // 2
        
        total_sum += np.exp(2j * np.pi * h * r_w / K)
        
    return total_sum

def compute_I_h_dp(M, h):
    K = 1 << M
    K2 = 1 << (M + 1)
    total_sum = 0j
    pow3 = [pow(3, i, K2) for i in range(M+1)]
    pow3_inv = [pow(pow3[i], -1, K2) for i in range(M+1)]
    
    for d in range(1, M + 1):
        a = (h * pow3_inv[d]) % K2
        
        # Base phase from 2^M, 3^{-1}, 1
        inv3_K2 = pow(3, -1, K2)
        base_num = ((1 << M) * pow3_inv[d] - inv3_K2 - 1) % K2
        # Note: base_num must be even
        assert base_num % 2 == 0
        base_phase = (h * (base_num // 2)) % K
        base_phase_float = 2 * np.pi * base_phase / float(K)
        
        dp = [0j] * (M + 1)
        dp[0] = 1.0 + 0j
        
        for j in range(1, d):
            next_dp = [0j] * (M + 1)
            # - a * 3^{d-1-j}
            xi_j_num = (-a * pow3[d - 1 - j]) % K2
            
            prefix_sum = 0j
            for S in range(j, M - (d - j) + 1):
                prefix_sum += dp[S - 1]
                p2 = (1 << S) % K2
                phase_num = (xi_j_num * p2) % K2
                assert phase_num % 2 == 0
                phase = 2 * np.pi * (phase_num // 2) / float(K)
                next_dp[S] = prefix_sum * np.exp(1j * phase)
            dp = next_dp
            
        prefix_sum = 0j
        for S in range(d - 1, M):
            prefix_sum += dp[S]
        total_sum += prefix_sum * np.exp(1j * base_phase_float)
        
    return total_sum

for M in range(2, 10):
    for h in [1, 2]:
        naive = compute_I_h_naive(M, h)
        dp = compute_I_h_dp(M, h)
        print(f"M={M}, h={h}: Naive={naive:.4f}, DP={dp:.4f}")
