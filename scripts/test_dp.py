import numpy as np

def compute_I_h_naive(M, h):
    K = 1 << (M - 1)
    
    def get_c_w(word):
        c = 0
        S = 0
        for a in word[:-1]:
            S += a
            c = c * 3 + 2**S
        c = c * 3 # wait, the formula is sum 3^{d-j} 2^{S_j}
        # let's use exact formula:
        S = 0
        d = len(word)
        c_w = 0
        for j in range(1, d):
            S += word[j-1]
            c_w += (3**(d-j)) * (2**S)
        return c_w

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
        inv3 = pow(3, -d, K)
        c_w = get_c_w(w)
        
        # rho_w = (2^M - c_w) 3^{-d} mod 2^{M+1}
        rho_w = ((1 << M) - c_w) * inv3 % (1 << (M+1))
        r_w = (rho_w - 1) // 2
        
        total_sum += np.exp(2j * np.pi * h * r_w / (1 << M))
        
    return total_sum

def compute_I_h_dp(M, h):
    K = 1 << (M + 1)
    total_sum = 0j
    pow3 = [pow(3, i, K) for i in range(M+1)]
    pow3_inv = [pow(pow3[i], -1, K) for i in range(M+1)]
    
    for d in range(1, M + 1):
        # Phase is h * r_w / 2^M
        # r_w = ( (2^M - c_w)*3^{-d} - 1 ) / 2 mod 2^M
        # So h * r_w / 2^M = h * (2^M - c_w) * 3^{-d} / 2^{M+1} - h / 2^{M+1}
        
        a = (h * pow3_inv[d]) % K
        base_phase = (a * (1 << M) - h) % K
        base_phase_float = 2 * np.pi * base_phase / float(K)
        dp = [0j] * (M + 1)
        dp[0] = 1.0 + 0j
        
        for j in range(1, d):
            next_dp = [0j] * (M + 1)
            xi_j_num = (-a * pow3[d - j]) % K
            
            prefix_sum = 0j
            for S in range(j, M - (d - j) + 1):
                prefix_sum += dp[S - 1]
                p2 = (1 << S) % K
                phase_num = (xi_j_num * p2) % K
                phase = 2 * np.pi * phase_num / float(K)
                next_dp[S] = prefix_sum * np.exp(1j * phase)
            dp = next_dp
            
        prefix_sum = 0j
        for S in range(d - 1, M):
            prefix_sum += dp[S]
        total_sum += prefix_sum * np.exp(1j * base_phase_float)
        
    return total_sum

for M in range(2, 10):
    for h in [1]:
        naive = compute_I_h_naive(M, h)
        dp = compute_I_h_dp(M, h)
        print(f"M={M}: Naive={naive:.4f}, DP={dp:.4f}")
