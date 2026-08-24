import numpy as np
import math

N_MAX = 10

def power_mod(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        base = (base * base) % mod
        exp //= 2
    return res

def mod_inverse(a, m):
    # Euler's theorem: a^{phi(m)-1} mod m
    # For m = 3^n, phi(3^n) = 2 * 3^{n-1}
    # But just brute force or pow is fine for small m
    # actually a is power of 2, so coprime to 3
    phi = 2 * (m // 3) if m > 1 else 1
    return power_mod(a, phi - 1, m)

def main():
    print("1.2 Cycle High-Mean Admissibility")
    print("Computing dimension D_1 and D_2 of the 3-adic offset measure at sigma = log2(3)")
    
    L23 = math.log2(3.0)
    
    # Q(a) = (1 - lambda) * lambda^{a-1}
    # Expected value of a under Q is 1 / (1 - lambda) = log2(3)
    # So 1 - lambda = 1 / log2(3) => lambda = 1 - 1/log2(3)
    lam = 1.0 - 1.0 / L23
    
    print(f"Target mean shift sigma = {L23:.5f}")
    print(f"Tilted geometric parameter lambda = {lam:.5f}")
    
    print(f"\n{'n':>3} | {'States':>6} | {'D_1 (Shannon)':>15} | {'D_2 (Collision)':>15}")
    print("-" * 47, flush=True)
    
    import csv
    with open('admissibility_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['n', 'D1', 'D2'])
        
        for n in range(1, N_MAX + 1):
            mod = 3**n
            valid_states = [x for x in range(mod) if x % 3 != 0]
            num_states = len(valid_states)
            idx = {x: i for i, x in enumerate(valid_states)}
            
            P = np.zeros((num_states, num_states))
            
            # Period of 2^a mod 3^n is phi(3^n)
            phi = 2 * (3**(n-1))
            
            # Precompute sum of Q(a) for a in each congruence class mod phi
            # Q(a = k + j*phi) = (1-lam) * lam^{k-1 + j*phi}
            # sum_j Q(a) = (1-lam) * lam^{k-1} / (1 - lam^phi)
            # for k in 1..phi
            
            Q_mod = np.zeros(phi)
            denom = 1.0 - lam**phi
            for k in range(1, phi + 1):
                Q_mod[k % phi] = (1.0 - lam) * (lam**(k - 1)) / denom
                
            for v in valid_states:
                u = idx[v]
                for k in range(1, phi + 1):
                    # a = k
                    inv2 = mod_inverse(power_mod(2, k, mod), mod)
                    v_next = ((3 * v + 1) * inv2) % mod
                    v_next_idx = idx[v_next]
                    
                    P[u, v_next_idx] += Q_mod[k % phi]
                    
            # Power iteration
            pi = np.ones(num_states) / num_states
            for _ in range(1000):
                pi_next = pi @ P
                if np.max(np.abs(pi_next - pi)) < 1e-12:
                    pi = pi_next
                    break
                pi = pi_next
            
            # Shannon entropy H = -sum pi * log3(pi)
            # D_1 = H / n
            pi_pos = pi[pi > 1e-12]
            H = -np.sum(pi_pos * np.log(pi_pos) / np.log(3.0))
            D1 = H / n
            
            # Collision entropy H2 = -log3(sum pi^2)
            # D_2 = H2 / n
            H2 = -np.log(np.sum(pi**2)) / np.log(3.0)
            D2 = H2 / n
            
            print(f"{n:3d} | {num_states:6d} | {D1:15.6f} | {D2:15.6f}", flush=True)
            writer.writerow([n, D1, D2])
            
    print("\nCheck complete. Observe if D_1 drops below 1.")

if __name__ == "__main__":
    main()
