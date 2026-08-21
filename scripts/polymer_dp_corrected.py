import numpy as np
import math

def build_joint_dist(max_k=30, max_S=250):
    p_X = {}
    for b in range(2, max_S + 1):
        if b == 3: continue
        p_X[b] = (4 * (b - 1)) / (3 * (2**b))
    
    dist_S = {1: {3: 1.0}}
    for k in range(2, max_k + 1):
        dist_S[k] = {}
        for s_prev, p_prev in dist_S[k-1].items():
            for x, p_x in p_X.items():
                s_new = s_prev + x
                if s_new <= max_S:
                    dist_S[k][s_new] = dist_S[k].get(s_new, 0.0) + p_prev * p_x
                    
    joint_dist = {}
    for k in range(1, max_k + 1):
        p_k = (0.75**(k-1)) * 0.25
        for S, p_S in dist_S[k].items():
            joint_dist[(k, S)] = p_k * p_S
            
    return joint_dist

def is_white(j, l, s, n, eps):
    j, l, s, n = int(j), int(l), int(s), int(n)
    power = n - 2*j + 2
    if power <= 0: return True 
    mod = 3**power
    num = pow(2, s - l + 1, mod)
    theta = num / mod
    if theta > 0.5: theta -= 1.0
    return abs(theta) > eps

def compute_free_energy_corrected(n, s, eps, joint_dist):
    max_j = n // 2
    max_l = 20 * max_j 
    
    l_values = np.arange(0, max_l + 1)
    l_to_idx = {l: idx for idx, l in enumerate(l_values)}
    
    Q = np.ones((max_j + 2, len(l_values)))
    eta = eps ** 3
    
    for j in range(max_j, -1, -1):
        for l_idx, l in enumerate(l_values):
            white_factor = math.exp(-eta) if is_white(j, l, s, n, eps) else 1.0
            expected_Q = 0.0
            
            for (k, S), p in joint_dist.items():
                new_j = j + k
                new_l = l + S
                if new_j > max_j or new_l > max_l:
                    Q_next = 1.0 
                else:
                    Q_next = Q[new_j, l_to_idx[new_l]]
                expected_Q += p * Q_next
                
            expected_Q += (0.75**30) * 1.0
            Q[j, l_idx] = white_factor * expected_Q
            
    Q_00 = Q[0, 0]
    if Q_00 <= 0: return None, Q_00
    F = -math.log(Q_00) / n
    return F, Q_00

if __name__ == "__main__":
    print("Building exact 2D joint distribution...")
    joint_dist = build_joint_dist(max_k=30, max_S=250)
    
    n = 100
    eps = 0.05
    
    print(f"\n=== Stage 4: Worst-Case Frequency Search (n={n}, eps={eps}) ===")
    print("Scanning s around the resonance (n * log2(3) ~ 158.5)...")
    
    results = []
    for s in range(140, 171):
        F, Q_00 = compute_free_energy_corrected(n, s, eps, joint_dist)
        if F is not None:
            results.append((s, F, Q_00))
            print(f"s={s:3d} | s/n={s/n:.3f} | F(nats)={F:.6f} | Q(0,0)={Q_00:.4e}")
            
    worst_s = min(results, key=lambda x: x[1])
    print(f"\n[!] Worst-case frequency found at s = {worst_s[0]} (s/n = {worst_s[0]/n:.3f})")
    print(f"    Minimum Free Energy F = {worst_s[1]:.6f} nats/step")
    
    with open('worst_s.txt', 'w') as f:
        f.write(str(worst_s[0]))
