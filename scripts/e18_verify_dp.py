import numpy as np

def brute_force(M, h):
    mod_exact = 1 << (M + 1)
    ans = 0j
    
    def dfs(d, current_S, current_c):
        nonlocal ans
        if current_S == M:
            # valid composition
            inv3_d = pow(3, -d, mod_exact)
            rho_w = (((1 << M) - current_c) * inv3_d) % mod_exact
            r_w = (rho_w - 1) // 2
            ans += np.exp(2j * np.pi * h * r_w / (1 << M))
            return
            
        for a in range(1, M - current_S + 1):
            next_S = current_S + a
            next_c = current_c + (1 << current_S) * (3 ** (d))
            # Wait, c_w definition:
            # In Collatz, c_{k+1} = 3 c_k + 2^{S_k}.
            # Let's use the exact definition of Collatz c_w!
            dfs(d + 1, next_S, current_c)
            
    # wait, the exact Collatz c_w recurrence:
    # c_0 = 0
    # c_k = 3 c_{k-1} + 2^{S_{k-1}}
    
    def dfs2(d, current_S, current_c):
        nonlocal ans
        if current_S == M:
            inv3_d = pow(3, -d, mod_exact)
            rho_w = (((1 << M) - current_c) * inv3_d) % mod_exact
            r_w = (rho_w - 1) // 2
            ans += np.exp(2j * np.pi * h * r_w / (1 << M))
            return
            
        for a in range(1, M - current_S + 1):
            next_S = current_S + a
            next_c = 3 * current_c + (1 << current_S)
            dfs2(d + 1, next_S, next_c)
            
    dfs2(0, 0, 0)
    return ans

from e17_no_overflow import compute_I_log

for M in [10, 15, 20]:
    I_brute = brute_force(M, 1)
    log_brute = np.log2(abs(I_brute))
    log_dp = compute_I_log(M, 1)
    print(f"M={M}: Brute={log_brute:.4f}, DP={log_dp:.4f}")
