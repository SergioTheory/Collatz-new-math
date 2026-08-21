import numpy as np
import math

def build_joint_dist(max_k=30, max_S=250):
    p_X = {b: (4 * (b - 1)) / (3 * (2**b)) for b in range(2, max_S + 1) if b != 3}
    dist_S = {1: {3: 1.0}}
    for k in range(2, max_k + 1):
        dist_S[k] = {}
        for s_prev, p_prev in dist_S[k-1].items():
            for x, p_x in p_X.items():
                if s_prev + x <= max_S:
                    dist_S[k][s_prev + x] = dist_S[k].get(s_prev + x, 0.0) + p_prev * p_x
    joint_dist = {}
    for k in range(1, max_k + 1):
        p_k = (0.75**(k-1)) * 0.25
        for S, p_S in dist_S[k].items():
            joint_dist[(k, S)] = p_k * p_S
    return list(joint_dist.keys()), list(joint_dist.values())

def is_white(j, l, s, n, eps):
    j, l, s, n = int(j), int(l), int(s), int(n)
    power = n - 2*j + 2
    if power <= 0: return True 
    mod = 3**power
    num = pow(2, s - l + 1, mod)
    theta = num / mod
    if theta > 0.5: theta -= 1.0
    return abs(theta) > eps

def compute_free_energy_fast(n, s, eps, keys, probs):
    max_j = n // 2
    max_l = 20 * max_j 
    l_values = np.arange(0, max_l + 1)
    Q = np.ones((max_j + 2, len(l_values)))
    eta = eps ** 3
    tail_p = 0.75**30
    
    # Pre-unpack
    K_vals = np.array([k for k, _ in keys])
    S_vals = np.array([S for _, S in keys])
    P_vals = np.array(probs)
    
    for j in range(max_j, -1, -1):
        wf = np.array([math.exp(-eta) if is_white(j, l, s, n, eps) else 1.0 for l in l_values])
        expected_Q = np.zeros(len(l_values))
        for i in range(len(K_vals)):
            k = K_vals[i]
            S = S_vals[i]
            p = P_vals[i]
            new_j = j + k
            if new_j > max_j:
                expected_Q += p
            else:
                # new_l = l_idx + S
                # valid if l_idx + S <= max_l  => l_idx <= max_l - S
                max_valid_idx = min(len(l_values) - 1, max_l - S)
                if max_valid_idx >= 0:
                    expected_Q[:max_valid_idx+1] += p * Q[new_j, S:S+max_valid_idx+1]
                    expected_Q[max_valid_idx+1:] += p
                else:
                    expected_Q += p
        expected_Q += tail_p
        Q[j, :] = wf * expected_Q
            
    Q_00 = Q[0, 0]
    return (-math.log(Q_00) / n if Q_00 > 0 else None), Q_00

if __name__ == "__main__":
    keys, probs = build_joint_dist()
    n = 100
    eps = 0.05
    results = []
    print("Scanning...")
    for s in range(140, 171):
        F, Q_00 = compute_free_energy_fast(n, s, eps, keys, probs)
        results.append((s, F, Q_00))
        print(f"s={s:3d} | s/n={s/n:.3f} | F(nats)={F:.6f} | Q(0,0)={Q_00:.4e}")
    worst_s = min(results, key=lambda x: x[1])
    print(f"\n[!] Worst-case frequency at s = {worst_s[0]}")
    print(f"    Minimum F = {worst_s[1]:.6f} nats/step")
    with open('worst_s.txt', 'w') as f:
        f.write(str(worst_s[0]))
