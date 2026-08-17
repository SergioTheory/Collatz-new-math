import numpy as np
import time
import math

def compute_lambda(n, s_values, A_max=1000):
    N = 3**n
    valid_1 = np.array([x for x in range(N) if x % 3 == 1], dtype=np.int64)
    valid_2 = np.array([x for x in range(N) if x % 3 == 2], dtype=np.int64)
    
    lambdas = []
    
    # We will compute the stationary measure for the last s (which is closest to 1, usually)
    # to evaluate Fourier decay. Or we can just compute it for s=0 (which is the actual tree measure).
    # The LDP involves the tilted measure, but s=0 is the standard reverse measure.
    V_stat_s0 = None
    
    # Precompute powers of 2 modulo N*3
    p2_mod = [pow(2, a, N*3) for a in range(A_max + 10)]
    
    for s in s_values:
        V_full = np.zeros(N, dtype=np.float64)
        V_full[valid_1] = 1.0 / (2 * 3**(n-1))
        V_full[valid_2] = 1.0 / (2 * 3**(n-1))
        
        rho_old = 0.0
        for it in range(2000):
            V_next = np.zeros(N, dtype=np.float64)
            
            # a0 = 1 (for x = 2 mod 3)
            for k in range(A_max // 2):
                a = 1 + 2 * k
                Y = (valid_2 * p2_mod[a] - 1) // 3 % N
                weight = 2.0 ** ((s - 1.0) * a)
                np.add.at(V_next, Y, V_full[valid_2] * weight)
                
            # a0 = 2 (for x = 1 mod 3)
            for k in range(A_max // 2):
                a = 2 + 2 * k
                Y = (valid_1 * p2_mod[a] - 1) // 3 % N
                weight = 2.0 ** ((s - 1.0) * a)
                np.add.at(V_next, Y, V_full[valid_1] * weight)
                
            # Tail mass
            a_tail_1 = 1 + 2 * (A_max // 2)
            a_tail_2 = 2 + 2 * (A_max // 2)
            
            w_tail_1 = (2.0 ** ((s - 1.0) * a_tail_1)) / (1.0 - 2.0 ** (2.0 * (s - 1.0)))
            w_tail_2 = (2.0 ** ((s - 1.0) * a_tail_2)) / (1.0 - 2.0 ** (2.0 * (s - 1.0)))
            
            tail_mass = np.sum(V_full[valid_2]) * w_tail_1 + np.sum(V_full[valid_1]) * w_tail_2
            
            V_next[valid_1] += tail_mass / (2 * 3**(n-1))
            V_next[valid_2] += tail_mass / (2 * 3**(n-1))
            
            rho = np.sum(V_next)
            V_full = V_next / rho
            
            if abs(rho - rho_old) < 1e-13:
                break
            rho_old = rho
            
        lambdas.append(math.log2(rho))
        if abs(s - 0.0) < 1e-5:
            V_stat_s0 = V_full.copy()
            
    return np.array(lambdas), V_stat_s0

def main():
    s_values = np.concatenate([np.linspace(-20, -0.1, 40), np.linspace(0.0, 0.98, 40)])
    
    lambdas_all = {}
    V_stat_all = {}
    
    for n in [8, 9, 10, 11]:
        t0 = time.time()
        print(f"Computing n={n}...")
        lams, V_stat = compute_lambda(n, s_values)
        lambdas_all[n] = lams
        V_stat_all[n] = V_stat
        print(f"  done in {time.time() - t0:.2f}s")
        
    print("\nVerification of Spectral Gap (n=8 vs n=9):")
    diff = np.max(np.abs(lambdas_all[9] - lambdas_all[8]))
    print(f"  Max |Lambda_9 - Lambda_8| = {diff:.4e}  (< 10^-12 expected)")
    
    print("\nExtracting I_rev(sigma):")
    sigmas = [1.0, 1.33, 1.5, 2.0]
    
    # Use n=11 for best approximation
    L11 = lambdas_all[11]
    
    for sig in sigmas:
        # I_rev(sigma) = sup_s (s * sigma - Lambda(s))
        I_rev = np.max(s_values * sig - L11)
        print(f"  I_rev({sig}) = {I_rev:.4f}")
        
    # Fourier decay for n=11 at s=0 measure
    print("\nFourier decay of stationary measure (s=0) for n=11:")
    V_s0 = V_stat_all[11]
    if V_s0 is not None:
        N = 3**11
        # Compute FFT
        fft_V = np.fft.fft(V_s0)
        # Check specific frequencies like 1, 3, 9, 27, 81 ...
        for p in range(12):
            freq = 3**p
            if freq < N:
                amp = np.abs(fft_V[freq])
                print(f"  |mu_hat(3^{p})| = {amp:.4e}")

if __name__ == '__main__':
    main()
